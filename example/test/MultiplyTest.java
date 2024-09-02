import org.junit.Test;
import org.junit.Before;
import org.junit.After;
import static org.junit.Assert.*;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.PrintStream;
import java.io.InputStream;

public class MultiplyTest {

    private final ByteArrayOutputStream outContent = new ByteArrayOutputStream();
    private final PrintStream originalOut = System.out;
    private final InputStream originalIn = System.in;

    @Before
    public void setUpStreams() {
        System.setOut(new PrintStream(outContent));
    }

    @Before
    public void setUpInput() {
        System.setIn(new ByteArrayInputStream("3".getBytes()));
    }

    @After
    public void restoreStreams() {
        System.setOut(originalOut);
        System.setIn(originalIn);
    }

    @Test
    public void testMain() {
        Multiply.main(new String[0]);
        assertEquals("output should be 6", 
            "Enter an integer value for x: x doubled is: 6", 
            outContent.toString().trim());
    }

    @Test
    public void testMultiply() {
        int x = Multiply.multiply(-3, 4);
        assertEquals("error in multiply", -12, x);
    }

    @Test
    public void testRepeated1() {
        int x = Multiply.multiply(2, 3);
        assertEquals("error in multiply", 6, x);
    }

    @Test
    public void testRepeated2() {
        int x = Multiply.multiply(2, 4);
        assertEquals("error in multiply", 8, x);
    }

    @Test
    public void testRepeated3() {
        int x = Multiply.multiply(2, 5);
        assertEquals("error in multiply", 10, x);
    }
}