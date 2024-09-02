// Name:
// CSCI 201 Lab 1
import java.util.concurrent.TimeUnit;

public class HelloWorld {
  public static void main(String[] args) {
    System.out.println("Hello, world!");
    try {
      TimeUnit.SECONDS.sleep(20);
    } catch (InterruptedException e) {
      Thread.currentThread().interrupt();
    }
  }
}
