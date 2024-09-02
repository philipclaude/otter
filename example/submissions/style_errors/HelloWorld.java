// Name:
// CSCI 201 Lab 1

public class HelloWorld {
  static int Y = 2;
  // TodoCommentCheck
  // TODO: define main method that prints "Hello, world!"
  // javadoc.MissingJavadocMethodCheck
  public static void main(String[] args) {
    System.out.println("Hello, world!");

    int i;

    // for( -> whitespace.WhitespaceAfterCheck
    // i++){ -> whitespace.WhitespaceAroundCheck
    // { } -> blocks.EmptyBlockCheck
    for(i = 0; i < 2; i++){ }

    // a is unused: coding.UnusedLocalVariableCheck
    int[] a = new int[] {1, 2,
        3}; // indentation.IndentationCheck

    // there's a space at the end of the next line -> regexp.RegexpSinglelineCheck
    for (i = 0; i < 5; i++); // blocks.NeedBracesCheck

    // c is unused -> coding.UnusedLocalVariableCheck
    int b = 3, c = b; // coding.MultipleVariableDeclarationsCheck

    // ';' is preceded with whitespace -> whitespace.EmptyForInitializerPadCheck
    for ( ; i < 1; i++ ) { // i++ ) -> whitespace.ParenPadCheck
      System.out.println(i);
    }

    // coding.SimplifyBooleanExpressionCheck
    if (false || b == 3) {
      {} }

    String s = "hello";
    if (s == "hello") {} // should use "hello".equals(s) -> coding.StringLiteralEqualityCheck
  }

    // indentation.IndentationCheck and javadoc.MissingJavadocMethodCheck
    private void example1(int x) throws Exception {
      x = 2;
    int i = 0;
    while (i >= 0) {
      switch (i) {
        case 1:
          i++;
        case 11:
          i++;
        // no default -> coding.MissingSwitchDefaultCheck
      }
    }
  }

  private void example2(int a
  , int b) { // ',' should be on previous line -> whitespace.SeparatorWrapCheck 
  }

  private void example3 (int aParam) { // violation ''(' is preceded with whitespace'
    example2 (1, 2); // violation ''(' is preceded with whitespace'
  }
} // missing newline after this -> NewlineAtEndOfFileCheck