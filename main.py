from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import json


chrome_driver_path = '//opt/homebrew/bin/chromedriver'
service=ChromeService("/opt/homebrew/bin/chromedriver")

def init_driver():
    chrome_options = Options()
    #chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def get_css_selector(driver,element):
    return driver.execute_script("""
        function getElementCssSelector(element) {
            if (!(element instanceof Element)) return;

            var selectors = [];
            while (element.nodeType === Node.ELEMENT_NODE) {
                var selector = element.nodeName.toLowerCase();

                if (element.id) {
                    selector += '#' + element.id;
                    selectors.unshift(selector);
                    break;
                } else {
                    if (element.className) {
                        var classList = element.className.split(/\s+/).filter(Boolean).join('.');
                        if (classList) {
                            selector += '.' + classList;
                        }
                    }
                    var sibling = element, nth = 1;
                    while (sibling = sibling.previousElementSibling) {
                        if (sibling.nodeName.toLowerCase() === selector) nth++;
                    }
                    selector += ":nth-of-type(" + nth + ")";
                }

                selectors.unshift(selector);
                element = element.parentNode;
            }

            return selectors.join(" > ");
        }

        return getElementCssSelector(arguments[0]);
    """, element)

def get_xpath_selector(driver,element):
    xpath = driver.execute_script(
        """
        function absoluteXPath(element) {
            var comp, comps = [];
            var parent = null;
            var xpath = '';
            var getPos = function(element) {
                var position = 1, curNode;
                if (element.nodeType == Node.ATTRIBUTE_NODE) {
                    return null;
                }
                for (curNode = element.previousSibling; curNode; curNode = curNode.previousSibling) {
                    if (curNode.nodeName == element.nodeName) {
                        ++position;
                    }
                }
                return position;
            };
            if (element instanceof Document) {
                return '/';
            }
            for (; element && !(element instanceof Document); element = element.nodeType == Node.ATTRIBUTE_NODE ? element.ownerElement : element.parentNode) {
                comp = comps[comps.length] = {};
                switch (element.nodeType) {
                    case Node.TEXT_NODE:
                        comp.name = 'text()';
                        break;
                    case Node.ATTRIBUTE_NODE:
                        comp.name = '@' + element.nodeName;
                        break;
                    case Node.ELEMENT_NODE:
                        comp.name = element.nodeName;
                        break;
                }
                comp.position = getPos(element);
            }
            for (var i = comps.length - 1; i >= 0; i--) {
                comp = comps[i];
                xpath += '/' + comp.name.toLowerCase();
                if (comp.position !== null) {
                    xpath += '[' + comp.position + ']';
                }
            }
            return xpath;
        }
        return absoluteXPath(arguments[0]);
        """, element)
    return xpath


def get_element_text(driver,element):
    OWN_TEXT_SCRIPT = "if(arguments[0].hasChildNodes()){var r='';var C=arguments[0].childNodes;for(var n=0;n<C.length;n++){if(C[n].nodeType==Node.TEXT_NODE){r+=' '+C[n].nodeValue}}return r.trim()}else{return arguments[0].innerText}"
    parent_text = driver.execute_script(OWN_TEXT_SCRIPT, element)
    return parent_text
def build_element_tree(driver, element, exclude_selectors):
    # 检查元素是否在排除的CSS选择器列表中
    # for selector in exclude_selectors:
    #     if element.find_elements(By.CSS_SELECTOR, selector):
    #         return None

    tag_name = element.tag_name.lower()
    if tag_name in ['link','script','style','meta','br','table','head','img']:
        return None
    if element.get_attribute('id') in ['sitehead','footer']:
        return None

    for c in element.get_attribute('class').split():
        if c in ['article']:
            print(element)
            pass

    # 获取当前元素的CSS路径
    # css_path = get_css_selector(driver, element)

    #获取当前元素的xpath路径
    xpath = get_xpath_selector(driver, element)

    #pure_text = driver.execute_script("return arguments[0].textContent;", element).strip()

    # 构建当前元素的节点
    # node = {
    #     'tag': element.tag_name,
    #     'text': get_element_text(driver,element),
    #     'css_path': css_path
    # }

    # 构建当前元素的节点
    node = {
        'tag': element.tag_name,
        'text': get_element_text(driver,element),
        'xpath': xpath
    }

    # 递归构建子节点，跳过仅包含字符串类型内容的子节点
    children = []
    child_elements = element.find_elements(By.XPATH, './*')  # 使用XPath获取直接子元素
    for child in child_elements:
        child_node = build_element_tree(driver, child, exclude_selectors)
        if child_node:
            children.append(child_node)

    if not node['text'] and not children:
        return None

    if children:
        node['children'] = children

    print(node['text'])

    return node

def extract_page_tree(driver, exclude_selectors):
    body_element = driver.find_element(By.CSS_SELECTOR, 'body')
    return build_element_tree(driver, body_element, exclude_selectors)

def extract_novel_content(driver, title_selector, content_selector):
    title_element = driver.find_element(By.XPATH, title_selector)
    content_element = driver.find_element(By.XPATH, content_selector)
    title = title_element.text.strip()
    content = content_element.text.strip()
    return title, content

def click_next_page(driver, next_page_selector):
    try:
        next_page_element = driver.find_element(By.CSS_SELECTOR, next_page_selector)
        next_page_element.click()
        time.sleep(5)  # 等待页面加载并执行JavaScript
        return True
    except Exception as e:
        print(f"无法点击下一页按钮: {e}")
        return False

def main():
    #url = input("请输入小说第一章的网址: ")
    driver = init_driver()

    # 用户输入排除的页头和页脚的CSS选择器
    #exclude_selectors = input("请输入页头和页脚的CSS选择器列表（以逗号分隔）: ").split(',')

    # 初次爬取并提取页面树状结构


    url = "https://www.qimao.com/shuku/1699328-16837740850002/"
    exclude_selectors=[]

    driver.get(url)
    time.sleep(5)  # 等待页面加载并执行JavaScript
    page_tree = extract_page_tree(driver, exclude_selectors)

    print("页面的树状结构:")
    print(page_tree)

    # 用户选择标识符
    title_selector = input("请输入小说标题的xpath选择器: ")
    content_selector = input("请输入小说内容主体的xpath选择器: ")
    next_page_selector = input("请输入下一页按钮的xpath选择器: ")

    # 自动爬取所有章节
    while True:
        title, content = extract_novel_content(driver, title_selector, content_selector)
        print(f"标题: {title}")
        print(f"内容: {content}")
        print("-" * 80)

        # 点击下一页按钮
        if not click_next_page(driver, next_page_selector):
            break

    driver.quit()

def checkCss(url,titleS):
    driver=init_driver()
    driver.get(url)
    time.sleep(5)
    title_element = driver.find_element(By.CSS_SELECTOR, titleS)
    text=get_element_text(driver,title_element)
    print(text)

def checkXpath(url,titleS,contentS,nextS):
    driver=init_driver()
    driver.get(url)
    time.sleep(5)
    title_element = driver.find_element(By.XPATH, titleS)
    content_element = driver.find_element(By.XPATH, contentS)
    print(get_element_text(driver,title_element))
    print(get_element_text(driver, content_element))
    next_element = driver.find_element(By.XPATH, nextS)
    next_element.click()
    pass




if __name__ == "__main__":
    # url="https://www.jjwxc.net/onebook.php?novelid=3448151&chapterid=4"
    # titleS="/html[1]/body[1]/div[9]/div[2]/div[1]/div[2]/h2[1]"
    # contentS="/html[1]/body[1]/div[9]/div[2]/div[1]"
    # nextS="/html[1]/body[1]/div[9]/div[4]/span[1]/a[2]"

    # url="https://fanqienovel.com/reader/7276663560427471412"
    # titleS="“”//*[@id=\"app\"]/div/div/div/div[2]/div[1]/h1"""
    # contentS="//*[@id="app"]/div/div/div/div[2]/div[2]"
    # nextS="/html[1]/body[1]/div[9]/div[4]/span[1]/a[2]"

    #checkXpath(url,titleS,contentS,nextS)
    main()
