// Name:
// CSCI 201 Lab 1

import java.util.Scanner;

public class Multiply {
  /**
   * main
   * @param args
   */
  public static void main(String[] args) {
    Scanner scanner = new Scanner(System.in);
    int x;
    // prompt user for an integer value x
    System.out.print("Enter an integer value for x: ");
    x = scanner.nextInt();
    // make a call to multiply and report x doubled
    //System.out.println("x doubled is: " + multiply(x, 2));
    scanner.close();
  }
}
