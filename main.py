# encoding: utf-8
import time
import datetime
import random
# third party
from loguru import logger
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


USERNAME = ""      # 用户名
PASSWORD = ""    # 密码
PAY_PASSWORD = ""  # 默认为身份证后六位
TARGET_AREA = "粤海校区"  # 校区
TARGET_SPORT = "羽毛球"   # 运动类型
TARGET_TIMES = ["19:00-20:00", "20:00-21:00"] # 目标时间段["20:00-21:00", "21:00-22:00"]
# TOMORROW = "2025-11-26"  # 硬编码明天日期
TOMORROW = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d') # 默认选择第二天
logger.info(f"预约时间：{TOMORROW}，目标时间段：{TARGET_TIMES}, 用户名：{USERNAME}")




def initialize_driver():
    """初始化Chrome浏览器并导航到预约页面"""
    options = webdriver.ChromeOptions()
    options.proxy = Proxy({
        'proxyType': ProxyType.MANUAL,
        'httpProxy' : '127.0.0.1:7890',
        'httpsProxy': '127.0.0.1:7890'
    })
    driver = webdriver.Chrome(options=options)
    driver.get("https://ehall.szu.edu.cn/qljfwapp/sys/lwSzuCgyy/index.do#/sportVenue")
    return driver

def login_with_password(driver):
    """使用账号密码登录"""
    logger.info("正在使用账号密码登录...")
    try:
        username_input = WebDriverWait(driver, 8).until(
            EC.visibility_of_element_located((By.XPATH, "//input[@id='username']"))
        )
        username_input.clear()
        username_input.send_keys(USERNAME)
        logger.info("已输入账号")

        pwd_input = WebDriverWait(driver, 8).until(
            EC.visibility_of_element_located((By.XPATH, "//input[@id='password' and @type='password']"))
        )
        driver.execute_script("arguments[0].value = arguments[1];", pwd_input, PASSWORD)
        logger.info("已通过JS输入密码")

        WebDriverWait(driver, 8).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@id='login_submit']"))
        ).click()
        logger.info("已提交登录")
        time.sleep(1)
    except Exception as e:
        logger.exception(f"登录失败: {e}")
        raise

def select_yuehai_and_gym(driver):
    """选择粤海校区和一楼重量型健身"""
    logger.info(f"正在选择[{TARGET_AREA}]...")
    WebDriverWait(driver, 2).until(
        EC.element_to_be_clickable((By.XPATH, f"//div[contains(@class, 'bh-btn-primary') and contains(text(), '{TARGET_AREA}')]"))
    ).click()
    logger.info(f"已选择: {TARGET_AREA}")
    time.sleep(0.3)

    logger.info(f"正在选择[{TARGET_SPORT}]...")
    WebDriverWait(driver, 2).until(
        EC.element_to_be_clickable((By.XPATH, f"//div[contains(@class, 'text-wrapper-7') and text()='{TARGET_SPORT}']"))
    ).click()
    logger.info(f"已选择: {TARGET_SPORT}")
    time.sleep(0.3)

def select_tomorrow_date(driver):
    """选择明天日期，失败时重试"""
    while True:
        logger.info(f"正在选择日期 {TOMORROW}...")
        try:
            WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((By.XPATH, f"//*[contains(text(),'{TOMORROW}')]"))
            ).click()
            logger.info(f"已选择日期: {TOMORROW}")
            time.sleep(0.2)
            break
        except Exception as e:
            logger.warning(f"未找到日期 {TOMORROW}，刷新页面重试: {e}")
            driver.refresh()
            time.sleep(0.3)
            select_yuehai_and_gym(driver)

def process_payment(driver, time_slot):
    """处理支付流程"""
    try:
        pay_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(@class, 'j-row-pay') and contains(text(),'未支付')]"))
        )
        logger.info("检测到未支付按钮，点击...")
        pay_btn.click()
        logger.info("已点击未支付按钮，等待支付弹窗...")

        sport_pay_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'体育经费')]"))
        )
        logger.info("检测到体育经费支付按钮，点击...")
        sport_pay_btn.click()
        logger.info("已点击体育经费支付按钮，等待支付页面加载...")
        time.sleep(2)

        # 切换到支付窗口
        windows = driver.window_handles
        driver.switch_to.window(windows[-1])
        logger.info("已切换到支付窗口")

        # 点击“下一步”按钮
        try:
            next_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@id='btnNext']"))
            )
            driver.execute_script("arguments[0].scrollIntoView();", next_btn)
            next_btn.click()
            logger.info("已点击'下一步'按钮")
            time.sleep(2)
        except Exception as e:
            logger.exception(f"未找到'下一步'按钮: {e}")

        # 输入支付密码
        try:
            password_input = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@id='password' and @readonly='readonly']"))
            )
            password_input.click()
            logger.info("已点击密码输入框，弹出数字键盘")
            time.sleep(0.5)

            key_buttons = WebDriverWait(driver, 10).until(
                lambda d: d.find_elements(By.XPATH, "//input[contains(@class, 'key-button')]")
            )
            digit_map = {}
            import re
            for btn in key_buttons:
                class_attr = btn.get_attribute("class")
                match = re.search(r"key-(\d+)", class_attr)
                if match and match.group(1).isdigit():
                    digit_map[match.group(1)] = btn

            for digit in PAY_PASSWORD:
                btn = digit_map.get(digit)
                if btn:
                    driver.execute_script("arguments[0].click();", btn)
                    logger.info(f"已点击数字: {digit}")
                    time.sleep(0.3)
                else:
                    logger.info(f"未找到数字 {digit} 的按钮")
                    raise Exception(f"未找到数字 {digit} 的按钮")

            confirm_pay_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'确认支付') or @id='qrbtn']"))
            )
            logger.info("检测到确认支付按钮，点击...")
            confirm_pay_btn.click()
            logger.info(f"时间段 {time_slot} 支付完成！")
            time.sleep(3)
        except Exception as e:
            logger.exception(f"支付密码输入或确认失败: {e}")
    except Exception as e:
        logger.exception(f"支付流程异常，可能已支付或页面结构变化: {e}")

def try_select_time_and_court(driver):
    """尝试预约时间段和场地，成功一个即返回True，所有时间段不可用时返回False"""
    all_times_unavailable = True  # 跟踪是否所有时间段都不可用
    for t in TARGET_TIMES:
        logger.info(f"尝试预约时间段 {t}...")
        try:
            WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((By.XPATH, f"//*[contains(text(),'{t}') and not(contains(text(),'已满员')) and not(contains(text(),'体育课占用'))]"))
            ).click()
            logger.info(f"已选择时间段: {t}")
            time.sleep(0.2)
            all_times_unavailable = False  # 找到一个可用时间段
        except Exception:
            logger.warning(f"时间段 {t} 暂不可用，继续尝试下一个时间段...")
            continue  # 继续尝试下一个时间段

        logger.info("正在选择场地...")
        labels = driver.find_elements(By.XPATH, "//div[contains(@class, 'rectangle-3')]//label[@for]")
        court_labels = [label for label in labels if "一楼健身房" in label.text.strip()]

        if not court_labels:
            logger.warning(f"时间段 {t} 没有可用场地，继续尝试下一个时间段...")
            continue

        chosen_label = random.choice(court_labels)
        logger.info(f"已选择场地: {chosen_label.text.strip()}")

        try:
            driver.execute_script("arguments[0].scrollIntoView();", chosen_label)
            chosen_label.click()
            logger.info(f"已点击场地: {chosen_label.text.strip()}")
            time.sleep(0.2)

            logger.info("正在提交预约...")
            WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'提交预约') or contains(text(),'提交预订') or contains(text(),'预约')]"))
            ).click()
            logger.info(f"时间段 {t} 预约已提交！")

            process_payment(driver, t)
            logger.info(f"时间段 {t} 预约成功！")
            return True  # 成功预约，立即返回
        except Exception as e:
            logger.warning(f"时间段 {t} 场地选择或提交失败: {e}")
            continue  # 场地选择或提交失败，继续尝试下一个时间段

    if all_times_unavailable:
        logger.warning("所有时间段均不可用，刷新页面...")
        driver.refresh()
        time.sleep(0.3)
        reenter_to_booking_page(driver)
    return False

def reenter_to_booking_page(driver):
    """返回预约页面"""
    try:
        h2_text = driver.find_element(By.XPATH, "//h2").text
        if "我的预约" in h2_text:
            logger.info("当前在'我的预约'页面，导航到'体育场馆预约'...")
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//a[@href='#/sportVenue']"))
            ).click()
            logger.info("已点击'体育场馆预约'")
            time.sleep(0.5)
    except Exception as e:
        logger.exception(f"导航到预约页面失败: {e}")

    select_yuehai_and_gym(driver)
    select_tomorrow_date(driver)

def main():
    """主程序：自动化预约健身房"""
    driver = initialize_driver()
    try:
        login_with_password(driver)
        select_yuehai_and_gym(driver)
        select_tomorrow_date(driver)

        count = 1
        while True:
            logger.info(f"===== 第{count}轮尝试 =====")
            count += 1
            if try_select_time_and_court(driver):
                logger.info("成功预约一个时间段，脚本退出。")
                break
            logger.info("继续监控可用时间段...")
            time.sleep(1)

        input("预约流程已完成，按回车键退出并关闭浏览器...")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()