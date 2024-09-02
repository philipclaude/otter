"""
  otter: a mini Java auto-grader to use with GitHub Actions or Gradescope.

  (c) Philip Claude Caplan, 2024.

  Distributed under the Apache-2.0 license.
"""
import json
import subprocess
import time
import argparse
import os
import pathlib
from xml.dom.minidom import parse
import shutil
import zipfile

USE_SHELL = False
if os.name == 'nt':
  USE_SHELL = True
CAPTURE_OUTPUT = True

MAVEN_VERSION_MAJOR = 3
MAVEN_VERSION_MINOR = 9
MAVEN_VERSION_PATCH = 9

def get_if_not_default(data: dict, title: str, default_value):
  """Return a value stored in a dictionary if present,
  otherwise return the default value."""
  if title in data:
    return data[title]
  return default_value

def get_maven_path(otter_dir, always_download):
  """Gets the path to mvn, downloading Maven if not installed."""
  if shutil.which("mvn") is not None and not always_download:
    return "mvn" # Maven already installed on the system
  maven_version = f"{MAVEN_VERSION_MAJOR}.{MAVEN_VERSION_MINOR}.{MAVEN_VERSION_PATCH}"
  url_base = f"https://dlcdn.apache.org/maven/maven-{MAVEN_VERSION_MAJOR}"
  url = f"{url_base}/{maven_version}/binaries"
  filename = f"apache-maven-{maven_version}-bin.zip"
  mvn = os.path.join(otter_dir, f"apache-maven-{maven_version}", "bin", "mvn")
  if not os.path.exists(mvn) or always_download:
    # Maven has not been downloaded yet.
    print("Maven not found.")
    print("Please consider downloading Maven and adding the location of mvn to your PATH.")
    print(f"Downloading Maven from {url} ...")
    result = subprocess.run(["curl", "-O", f"{url}/{filename}"], shell=USE_SHELL, check=False)
    assert result.returncode == 0
    with zipfile.ZipFile(filename, "r") as z:
      z.extractall(otter_dir)
    result = subprocess.run(["chmod", "+x", mvn], shell=USE_SHELL, check=False)
  return mvn

class TestCaseResult:
  """Test case result."""
  def __init__(self, classname, method, t_run, max_points, visibility):
    self.classname = classname
    self.method = method
    self.time = t_run
    self.max_points = max_points
    self.visibility = visibility
    self.passed = False
    self.status = "failed"
    self.points = 0
    self.message = ""
    self.report = ""

  def set_result(self, passed, status, points, message, report = None):
    """Saves the test case result and any messages to print."""
    self.passed = passed
    self.status = status
    self.points = points
    self.message = message
    self.report = report

class CheckstyleError:
  """Style check result."""
  def __init__(self, file, line, message, check):
    self.file = file
    self.line = line
    self.message = message
    self.check = check

class MavenTestSuite:
  """A suite of tests that can be run with Maven."""
  def __init__(self, classname, setup):
    """Initialize the test case"""
    self.classname = classname
    self.info = get_if_not_default(setup, "info", "")
    self.max_time = get_if_not_default(setup, "timeout", None)
    self.points_per_test = get_if_not_default(setup, "points", 1)
    self.pkg = get_if_not_default(setup, "package", "")
    if self.pkg:
      self.pkg += "."
    self.visibility = get_if_not_default(setup, "visibility", "visible")
    self.results = [] # list of TestCaseResult
    self.total_points = 0

    # Enumerate all the methods that should be tested.
    if 'repeated' in setup and setup['repeated']:
      assert 'prefix' in setup
      assert 'start' in setup
      assert 'end' in setup
      prefix = setup['prefix']
      start = setup['start']
      end = setup['end']
      self.methods = [f"{prefix}{x}" for x in range(start, end + 1)]
    else:
      assert 'method' in setup
      self.methods = [setup["method"]]
    self.max_points = len(self.methods) * self.points_per_test


  def run(self, mvn_base, target_dir, verbose):
    """Runs the test case methods."""
    for method in self.methods:
      self.total_points += self.max_points
      cmd = mvn_base + [f"-Dtest={self.classname}#{method}", "test"]

      try:
        t_start = time.time()
        run_result = subprocess.run(cmd, shell=USE_SHELL, check=False,
                                    capture_output=CAPTURE_OUTPUT,
                                    timeout=self.max_time, text=True)
        result = TestCaseResult(self.classname, method, time.time() - t_start,
                                self.points_per_test, self.visibility)
        if run_result.returncode == 0:
          print(f"Test {self.classname}.{method} passed ({self.info}).")
          result.set_result(True, "success", self.points_per_test,
                            "Passed after {time.time() - t_start:.2f} seconds.")
        else:
          print(f"Test {self.classname}.{method} failed ({self.info}).")
          report_path = os.path.join(target_dir, f"surefire-reports/{self.pkg}{self.classname}.txt")
          if not os.path.exists(report_path):
            # This can happen if the test tries to call a method that doesn't exist.
            # So the submission compiles fine, but the test doesn't.
            # In this case, report the Maven output.
            message = run_result.stdout
          else:
            # Read the surefire report.
            with open(report_path, "r", encoding='utf-8') as report_file:
              message = report_file.read()
          result.set_result(False, "failed", 0, message, message)

      except subprocess.TimeoutExpired:
        dt = time.time() - t_start
        result = TestCaseResult(self.classname, method, dt,
                                self.points_per_test, self.visibility)
        print(f"Test {self.classname}.{method} timed out after {dt:.2f} seconds.")
        result.set_result(False, "failed", 0, "timeout", f"Timeout after {dt:.2f} seconds.")
      finally:
        pass
      if verbose and run_result:
        print(run_result.stdout)
      self.results.append(result)

def write_markdown_summary(filename, checks, compiler_report, test_results, style_errors):
  """Write a Markdown summary file which can be displayed in a GitHub workflow summary."""
  with open(filename, "w", encoding='utf-8') as f:
    if compiler_report:
      f.write(f"{os.linesep}{compiler_report}{os.linesep}")
      return # Do not report on test/style checks if there is a compile error.

    if checks in ("tests", "all"):
      # Write the table with test case status messages.
      n_test_errors = 0
      f.write(f"Class | Method | Time (s) | Status |{os.linesep}|---|---|---|---|{os.linesep}")
      for result in test_results:
        f.write(f"{result.classname} | {result.method} | {result.time:.2f} | "
                f"{result.status} |{os.linesep}")
        if not result.passed:
          n_test_errors += 1
      f.write(f"{os.linesep}Detected {n_test_errors} test case errors.{os.linesep}")

      # Write test error information.
      for result in test_results:
        if result.report:
          f.write(f"{os.linesep} <details><summary><b>"
                  f"{result.classname}.{result.method}</b></summary>{os.linesep}")
          lines = result.report.split(os.linesep)
          for line in lines:
            f.write(line + '<br/>' + os.linesep)
          f.write(f"</details>{os.linesep}")

    # Write style error information.
    if len(style_errors) and checks in ("style", "all"):
      f.write(f"{os.linesep}|File | Line | Message | Check |{os.linesep}"
              f"|---|---|---|---|{os.linesep}")
      for result in style_errors:
        f.write(f"| {result.file} | Line {result.line} | {result.message} | "
                f"{result.check} |{os.linesep}")
    f.write(f"{os.linesep}Detected {len(style_errors)} style errors.{os.linesep}")

def write_maven_configuration(config, pom_template, otter_dir, source_dir):
  """Write pom.xml in the otter_dir, inserting the necessary files into the
  sections for the maven-compiler-plugin and maven-checkstyle-plugin."""
  assert os.path.exists(pom_template)
  library = config['library']
  submission = config['submission']

  pom_xml = parse(pom_template)
  plugins = pom_xml.getElementsByTagName('plugin')
  for plugin in plugins:
    artifacts = plugin.getElementsByTagName('artifactId')
    for artifact in artifacts:
      xml_data = artifact.toxml()
      if "maven-compiler-plugin" in xml_data:
        includes = artifact.parentNode.getElementsByTagName("includes")
        for source in library:
          include = pom_xml.createElement("include")
          include.appendChild(pom_xml.createTextNode(f"{source_dir}{source}"))
          includes[0].appendChild(include)
      if "maven-checkstyle-plugin" in xml_data:
        includes = artifact.parentNode.getElementsByTagName("includes")
        sources = ""
        for j, source in enumerate(submission):
          sources += source_dir + source
          if j < len(submission) - 1:
            sources += ","
        includes[0].appendChild(pom_xml.createTextNode(sources))

  # Write the configuration file.
  with open(otter_dir / "pom.xml", "w", encoding="utf-8") as fp:
    pom_xml.writexml(fp)

def main():
  """Runs the main program."""

  # Parse command-line arguments.
  parser = argparse.ArgumentParser()
  parser.add_argument("--config", type=str, default="test/config.json",
                      help='path of input tests JSON file')
  parser.add_argument("--source", type=str, default="",
                      help="location of source submission files")
  parser.add_argument("--check", type=str, default="all",
                      help="options: tests, style or all (tests and style)")
  parser.add_argument("--markdown", type=str, default="results.md",
                      help="path of output results Markdown file")
  parser.add_argument("--gradescope", action='store_true',
                      help='output results.json file for gradescope')
  parser.add_argument("--clean", action='store_true',
                      help='delete all temporary build files')
  parser.add_argument("--verbose", action='store_true', help="show additional output")
  args = parser.parse_args()

  # Get the directory this script is in and the Maven configuration file.
  otter_dir =  pathlib.Path(__file__).parent.resolve()
  pom = os.path.join(otter_dir, "pom.xml")
  pom_template = os.path.join(otter_dir, "pom_template.xml")
  test_dir = pathlib.Path("test")
  tmp_dir = otter_dir / "tmp"
  target_dir = otter_dir / "target"
  source_dir = args.source
  if source_dir and source_dir[-1] != os.sep:
    source_dir += os.sep
  mvn = get_maven_path(otter_dir, always_download=False)

  # Load the configuration file
  with open(args.config, "r", encoding="utf-8") as fconfig:
    config = json.loads(fconfig.read())
  assert config

  # Write the Maven project configuration.
  write_maven_configuration(config, pom_template, otter_dir, source_dir)
  mvn_base = [f"{mvn}", "-q", "-f", pom]

  if args.clean:
    # Cleanup!
    subprocess.run(mvn_base + ["clean"], shell=USE_SHELL, check=False,
                   capture_output=CAPTURE_OUTPUT)
    shutil.rmtree(tmp_dir, ignore_errors=True)
    shutil.rmtree(target_dir, ignore_errors=True)
    return

  # First check that the submission compiles.
  compiler_result = subprocess.run(mvn_base + ["compile"],  shell=USE_SHELL,
                                   check=False, capture_output=CAPTURE_OUTPUT)
  compiler_report = None
  if compiler_result.returncode != 0:
    compiler_report = compiler_result.stdout.decode("utf-8")
    print(compiler_report)

  style_results = []
  max_style_points = 0
  style_points = 0
  style_report = ""
  if args.check in ("all", "style") and not compiler_report:
    # Load the JSON information about style checks.
    style = config['style']

    # Extract information.
    max_style_points = get_if_not_default(style, 'points', 0)
    checks = get_if_not_default(style, 'checks', ['all'])
    submission = config['submission']

    # Run the style checker.
    cmd = mvn_base + ["checkstyle:checkstyle"]
    try:
      result = subprocess.run(cmd, shell=USE_SHELL, capture_output=CAPTURE_OUTPUT, check=False)
      if result.returncode == 0:
        # Read the checkstyle result.
        document = parse(os.fspath(target_dir / "checkstyle-result.xml"))
        files = document.getElementsByTagName('file')

        # Process checkstyle errors.
        n_errors = 0
        for f in files:
          # Is this a file we want to include?
          filename = f.getAttribute('name').split(os.sep)[-1]
          if 'all' not in submission and filename not in submission:
            continue

          # Retrieve style errors.
          errors = f.getElementsByTagName('error')
          for e in errors:
            # Retrieve information about the style error.
            line = e.getAttribute('line')
            msg = e.getAttribute('message')
            source = e.getAttribute('source').split('.checks.')[-1]

            # Is this a check we want to include?
            if source in checks or 'all' in checks:
              n_errors += 1
              info = f"Style error in {filename} (line {line}): {msg} ({source})"
              style_report += info + os.linesep
              result = CheckstyleError(filename, line, info, source)
              style_results.append(result)
          if n_errors == 0:
            style_points = max_style_points
      else:
        style_report = result.stdout.decode(encoding="utf-8")
    except Exception as e: # pylint: disable=broad-except
      print("Exception during style check: ", e)
    print(style_report)

  test_results = []
  max_test_points = 0
  test_points = 0
  if args.check in ("all", "tests") and not compiler_report:
    # The test config file contains a list of classes,
    # and each class has a list of tests.
    # Really it should be called a test "suite", particularly
    # if the test is "repeated" such as "sample_test1", "sample_test2", etc.
    for class_info in config["tests"]["classes"]:

      # Extract the class name and the list of tests
      classname = class_info["class"]
      tests = class_info["tests"]

      # Run test cases
      for setup in tests:

        # Clean up the tmp directory and copy the test class file
        shutil.rmtree(tmp_dir, ignore_errors=True)
        os.mkdir(tmp_dir)
        shutil.copy(test_dir / f"{classname}.java", tmp_dir)

        # Run the test suite, saving the case object which will hold a list of results
        test_suite = MavenTestSuite(classname, setup)
        test_suite.run(mvn_base, target_dir, args.verbose)
        max_test_points += test_suite.max_points
        for result in test_suite.results:
          test_results.append(result)
          test_points += result.points

  # Accumulate all the results and write the output files.
  max_points = max_style_points + max_test_points
  points = test_points + style_points
  if max_points > 0:
    print(f"{os.linesep}Points: {points} (/ {max_points}){os.linesep}")
  else:
    print(f"{os.linesep}Points: {points}{os.linesep}")

  write_markdown_summary(args.markdown, args.check, compiler_report, test_results, style_results)
  if args.gradescope:
    tests = []

    if compiler_report:
      tests.append({
      "score": 0,
      "status": "failed",
      "name": "Compiler Check",
      "name_format": "text",
      "output": compiler_report,
      "output_format": "text",
      "visibility": "visible"
    })

    for result in test_results:
      test = {
        "score": result.points,
        "max_score": result.max_points,
        "status": result.status,
        "name": f"{result.classname}.{result.method}",
        "name_format": "text",
        "output": result.report if result.report else "",
        "output_format": "text",
        "visibility": result.visibility
      }
      tests.append(test)

    if max_style_points > 0:
      tests.append({
        "score": style_points,
        "max_score": max_style_points,
        "status": "passed" if style_points == max_style_points else "failed",
        "name": "Style Check",
        "name_format": "text",
        "output": style_report,
        "output_format": "text",
        "visibility": "visible"
      })

    gradesceope_results = {
      "score": points,
      "stdout_visibility": "visible",
      "tests": tests
    }

    with open("results.json", "w", encoding='utf-8') as f:
      json.dump(gradesceope_results, f, indent=2)

if __name__ == "__main__":
  main()
