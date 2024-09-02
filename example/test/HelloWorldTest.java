import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import static org.junit.Assert.assertEquals;

import java.io.ByteArrayOutputStream;
import java.io.PrintStream;

public class HelloWorldTest {

    private final ByteArrayOutputStream outContent = new ByteArrayOutputStream();
    private final PrintStream originalOut = System.out;

    @Before
    public void setUpStreams() {
      System.setOut(new PrintStream(outContent));
    }

    @After
    public void restoreStreams() {
      System.setOut(originalOut);
    }

    @Test
    public void testMain() {
        HelloWorld.main(new String[0]);
    }

    @Test
    public void testOutput() {
        HelloWorld.main(new String[0]);
        assertEquals("output should be Hello, world!", 
                     "Hello, world!", outContent.toString().trim());
    }

    @Test(timeout = 1000)
    public void testTimeout() throws InterruptedException {
      HelloWorld.main(new String[0]);
    }
}