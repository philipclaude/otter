# `otter`

`otter` is a simple auto-grading system currently designed to be used for `Java` programming assignments in CSCI 201 (Data Structures) at Middlebury College. The name `otter` is short for auto-grader.
There is also a river that runs through Middlebury called Otter Creek which is another reason I picked the name.

## Motivation

There are already some great tools out there for auto-grading tests with `Java` and Gradescope (see [jh61b](https://github.com/ucsb-gradescope-tools/jh61b) and [jacquard](https://github.com/jacquard-autograder/jacquard) for a few examples), but I wanted a little more control over the output so that students have more feedback on why a check failed.
I also had a hard time deciding between using GitHub Actions (within assignment repositories) and Gradescope to do the auto-grading, so `otter` was designed to support both of these platforms (though I'm sure existing Gradescope-based tools could be extended to work with GitHub Actions as well).

I also wanted to make it easy to run the checks (unit tests and style checks) **locally** so that students can debug their assignment submissions before committing to GitHub (potentially using up a lot of minutes allocated to a GitHub Team) or uploading files to Gradescope.

## Dependencies

`otter` relies on `JUnit` and `Maven`.

On Mac, you can use either [Homebrew](https://brew.sh/) (`brew install maven`) or [MacPorts](https://ports.macports.org/) (`sudo port install maven3`) to install Maven.

For Windows, download the latest version of Maven for your system from [here](https://maven.apache.org/download.cgi) and then extract the archive.
You'll then need to set the **Environment Variables** `M2_HOME` and `MAVEN_HOME` to point to your extracted Maven folder and then the `PATH` to point to the `bin` directory in the extracted Maven folder.

For Linux (as is used on Gradescope and the GitHub Actions), run the `setup.sh` script in the `example` directory to install the dependencies.

If Maven is not found, `otter` will download it and use the resulting `mvn` script, but it is still recommended to have Maven installed on your system.

## Example

Before discussing how to configure your tests, let's run through an example of how to use `otter`.
After cloning the repository, navigate to the `example` directory.

The `example` directory contains some scripts that can be used to compile a Gradescope autograder as well as some `Java` files (`HelloWorld.java` and `Multiply.java`) that represent a submission from a student. These files are just copies of the files in `example/submissions/template`.

The `example/test` directory contains the test files (using `JUnit`) for the submission, as well as a configuration file (more on this soon). Tests can be written in pure `JUnit`, and there isn't a "runner" that needs to be set up like other autograding systems. `otter` will run each individual test using `Maven` and then analyze the return code and/or build output (depending on the success of the compile and test stages).

### Testing locally.

It's generally quicker to locally test an assignment submission passes all the checks locally compared to submitting it to GitHub or Gradescope. An example script to download the latest version of `otter` and then run all the checks (defined in `test/config.json`) is included in the `check` script:

```bash
./check
```

This will test `HelloWorld.java` and `Multiply.java` using the tests defined in the `test` directory. There should be some test failures and style errors reported in the output. To see further information about each test failure, open the `results.md` file (rendering the Markdown). Each failed unit test will appear as a collabsible section, and the expanded portion will display information about the failure.

Style check errors are also reported in `results.md` which is just a tabular version of what is displayed in the `otter` output.

#### Testing a different submission.

This section assumes you already ran the `check` script (because it assumes `otter` was downloaded and extracted to the `otter` directory within the `example` directory).
Instead of testing the submission defined in the `HelloWorld.java` and `Multiply.java` files of the current working directory, you can specify the `--source` directory where the submission is located (in this case the directory containing `HelloWorld.java` and `Multiply.java`). For example, to test the submission in `submisions/full_points` (no errors or test failures):

```bash
python3 otter/otter.py --check all --source submissions/full_points
```

Example submissions include:

- `compile_error`: compile error in the submission,
- `full_points`: a complete submission that passes unit tests and style checks,
- `missing_method`: submission compiles but the test does not compile because the submission is missing a method,
- `style_errors`: test cases pass but there are many style errors,
- `template`: the initial template distributed to students,
- `timeout`: test cases take too long to run.

### Testing with Gradescope.

(For instructors) To compile the Gradescope autograder for the `example`, again navigate to the `example` directory and type:

```bash
make autograder
```

The template (distributed to students) can be compiled with:

```bash
make name=example template
```

which will create `example.zip`. You can change the `name` passed to `make` to change the name of the resulting `zip`.

Then create an assignment in Gradescope and upload the generated `autograder.zip` file. **Be sure to pick the JDK 17 Base Image Variant when setting up the autograder.**

Then click on `Test Autograder` and upload `HelloWorld.java` and `Multiply.java` from one of the `submissions` directories.

### Testing with a GitHub Action.

Sample autograding  workflows are already set up within this repository. Specifically, there is a `Grader` workflow that can test a particular submission. It would require a few minor changes if used within a repository on GitHub Classroom, mostly where `otter` will look for the `.java` files.

Click on `Actions` and the click the `Grader` workflow (on the left pane). You should see a banner with the message "This workflow has a workflow_dispatch event trigger". Click on the `Run workflow` dropdown on the right and select which checks to run, then pick which submission to use (relative to the `example/submissions` directory). Click the `Run workflow` button and an Action should start running.

Click on the Action that just started running and, when the workflow is done, the `Summary` (at the top-left) of the Action should display the same Markdown file that was previously produced in the `Testing locally` section of this README.

## Configuration

Unit tests can be written using `JUnit` and the style checks are run using `checkstyle`. The style check is configured using a `checkstyle.xml` file, which should be included in your `test` directory. The checks that are configured in `checkstyle.xml` do not necessarily result in style errors. The style check errors that are reported as actual errors are configured in `config.json`.

Here is an example `config.json` (the same one in `example/test/config.json`):

```json
{
  "library": [
    "HelloWorld.java",
    "Multiply.java"
  ],
  "submission": [
    "HelloWorld.java",
    "Multiply.java"
  ],
  "tests": {
    "classes": [
      {
        "class": "HelloWorldTest",
        "tests": [
          {
          "method": "testMain",
          "info": "testing main runs",
          "timeout": 30,
          "points": 1
          },
          {
            "method": "testOutput",
            "info": "testing hello world message",
            "timeout": 30,
            "points": 2
          }
        ]
      },
      {
        "class": "MultiplyTest",
        "tests": [
          {
            "method": "testMain",
            "info": "testing multiply main",
            "timeout": 30,
            "points": 2
          },
          {
            "method": "testMultiply",
            "info": "testing multiplication function",
            "timeout": 30,
            "points": 2
          },
          {
            "repeated": true,
            "prefix": "testRepeated",
            "info": "testing multiplication",
            "start": 1,
            "end": 3,
            "points": 1
          }
        ]
      }
    ]
  },
  "style": {
    "points": 1,
    "checks": [
      "regexp.RegexpSinglelineCheck",
      "javadoc.MissingJavadocMethodCheck",
      "TodoCommentCheck",
      "NewlineAtEndOfFileCheck",
      "UnusedLocalVariable",
      "blocks.EmptyBlockCheck",
      "blocks.NeedBracesCheck",
      "blocks.LeftCurlyCheck",
      "coding.EmptyStatementCheck",
      "coding.MissingSwitchDefaultCheck",
      "coding.MultipleVariableDeclarationsCheck",
      "coding.SimplifyBooleanExpressionCheck",
      "coding.StringLiteralEqualityCheck",
      "coding.UnusedLocalVariableCheck",
      "indentation.IndentationCheck",
      "sizes.LineLengthCheck",
      "whitespace.MethodParamPadCheck",
      "whitespace.ParenPadCheck",
      "whitespace.WhitespaceAfterCheck",
      "whitespace.WhitespaceAroundCheck"
    ]
  }
}
```

The `library` field specifies ALL of the files to include in the assignment (i.e. the files a student submits + any helper files you might include in an assigment). The `submission` field simply specifies the student submission files.

The `tests` field specifies a list of classes to use for the tests (here, `HelloWorldTest` and `MultiplyTest`).
Within these, the public methods annotated as `@Test` can be listed to run as unit tests.
Those that are not listed here will not be used in the `otter` report.
The `timeout` can be specified in seconds and the number of points for a particular test can also be specified.
If your test names have a common prefix and are numbered (at the end) consecutively, e.g. (`test4`, `test5`, `test6`), you can use the `repeated` field to run a series of tests as in the example above with `testRepeated1`, `testRepeated2`, `testRepeated3`. In this case, the `points` field corresponds to the points assigned to **one** of these tests.

The number of points assigned to the style tests can also be included.
If you add "all" to the list of `"checks"`, then any style errors will be reported as errors.


## License

`otter` is distributed under the Apache-2.0 License.

Copyright 2024 Philip Claude Caplan

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.