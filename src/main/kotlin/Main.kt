import org.openqa.selenium.By
import org.openqa.selenium.JavascriptExecutor
import org.openqa.selenium.WebDriver
import org.openqa.selenium.WebElement
import org.openqa.selenium.chrome.ChromeDriver
import org.openqa.selenium.chrome.ChromeOptions
import org.openqa.selenium.support.ui.ExpectedConditions
import org.openqa.selenium.support.ui.WebDriverWait
import java.time.Duration

data class Node(
    val xpath: String,
    val text: String,
    val children: MutableList<Node> = mutableListOf()
)

fun initDriver(): WebDriver {
    System.setProperty("webdriver.chrome.driver", "/opt/homebrew/bin/chromedriver")
    val options = ChromeOptions()
    options.addArguments( "--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage","--remote-allow-origins=*")
    return ChromeDriver(options)
}


fun getText(driver: WebDriver, element: WebElement): String {
    var OWN_TEXT_SCRIPT = "if(arguments[0].hasChildNodes()){var r='';var C=arguments[0].childNodes;for(var n=0;n<C.length;n++){if(C[n].nodeType==Node.TEXT_NODE){r+=' '+C[n].nodeValue}}return r.trim()}else{return arguments[0].innerText}"
    val jsExecutor = driver as JavascriptExecutor
    return jsExecutor.executeScript(
        OWN_TEXT_SCRIPT, element
    ) as String
}

fun getXpath(driver: WebDriver, element: WebElement): String {
    val jsExecutor = driver as JavascriptExecutor
    return jsExecutor.executeScript(
        """
        function getXPath(element) {
            if (element.id !== '') {
                return 'id("' + element.id + '")';
            }
            if (element === document.body) {
                return element.tagName.toLowerCase();
            }
            var ix = 0;
            var siblings = element.parentNode.childNodes;
            for (var i = 0; i < siblings.length; i++) {
                var sibling = siblings[i];
                if (sibling === element) {
                    return getXPath(element.parentNode) + '/' + element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
                }
                if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
                    ix++;
                }
            }
            return '';
        }
        return getXPath(arguments[0]);
        """, element
    ) as String
}

fun buildElementTree(driver: WebDriver, element: WebElement): Node? {
    val tagName = element.tagName.lowercase()
    if (tagName in listOf("head", "link", "meta", "style", "script")) {
        return null
    }

    val text =getText(driver,element)
    val xpath = getXpath(driver, element)

    val node = Node(xpath, text)
    val childElements = element.findElements(By.xpath("./*"))

    for (child in childElements) {
        val childNode = buildElementTree(driver, child)
        if (childNode != null) {
            node.children.add(childNode)
        }
    }

    if (node.children.isEmpty() && node.text.isEmpty()) {
        return null
    }

    return node
}

fun waitForPageToLoad(driver: WebDriver) {
    WebDriverWait(driver, Duration.ofSeconds(30)).until { webDriver ->
        (webDriver as JavascriptExecutor).executeScript("return document.readyState") == "complete"
    }
}

fun extractPageTree(driver: WebDriver, url: String): Node? {
    driver.get(url)
    waitForPageToLoad(driver)
    val wait = WebDriverWait(driver, Duration.ofSeconds(10))
    wait.until(ExpectedConditions.presenceOfElementLocated(By.tagName("body")))
    val bodyElement = driver.findElement(By.tagName("body"))
    return buildElementTree(driver, bodyElement)
}

fun main() {
    val url = readLine() ?: return
    val driver = initDriver()
    val pageTree = extractPageTree(driver, url)
    driver.quit()

    println(pageTree)
}
