#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import logging
import pathlib
from typing import List, Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from selenium.webdriver import Edge, Chrome
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions


# ----------------------
# Configuration
# ----------------------
# 可通过环境变量覆盖：BMC_URL, BMC_USER, BMC_PASS, BROWSER, HEADLESS
BMC_URL: str = os.getenv("BMC_URL", "http://192.168.1.100/")
BMC_USERNAME: str = os.getenv("BMC_USER", "admin")
BMC_PASSWORD: str = os.getenv("BMC_PASS", "admin")
BROWSER: str = os.getenv("BROWSER", "edge").lower()  # 'edge' 或 'chrome'
HEADLESS: bool = os.getenv("HEADLESS", "1").lower() in ("1", "true", "yes")

# 页面控件的候选选择器（需要根据实际BMC页面调整，优先把最准确的放前面）
SELECTORS = {
    "username": [
        "input#username",
        "input[name='username']",
        "input[name='user']",
        "input[type='text']",
    ],
    "password": [
        "input#password",
        "input[name='password']",
        "input[type='password']",
    ],
    "login": [
        "button#login",
        "button[type='submit']",
        "input[type='submit']",
        "div.login-button",
        "div[role='button'].login",
        "button.btn.btn-primaryblock.full-width.m-b",
    ],
    # 负责开始采集的按钮（div 或 button）
    "collect": [
        "div#collect",
        "div.collect",
        "button#collect",
        "button.collect",
        "div[role='button'][data-action='collect']",
    ],
    # DOM 弹窗中的确认按钮（若不是浏览器原生 alert/confirm）
    "confirm": [
        "button#confirm",
        "button.confirm",
        "button[data-type='confirm']",
        "div.modal-footer button.btn-primary",
        ".modal-footer .btn-primary",
    ],
}

DEFAULT_TIMEOUT_SECONDS: int = 30


def configure_logging() -> None:
    script_path = pathlib.Path(__file__).resolve()
    log_path = script_path.with_suffix(".log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def create_webdriver() -> "object":
    """Create and return a Selenium WebDriver for Edge or Chrome using Selenium Manager."""
    if BROWSER == "chrome":
        options = ChromeOptions()
        if HEADLESS:
            options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1268,720")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-dev-shm-usage")
        driver = Chrome(options=options)
        return driver

    # default to Edge
    options = EdgeOptions()
    if HEADLESS:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1268,720")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-dev-shm-usage")
    driver = Edge(options=options)
    return driver


def wait_for_any_and_return(driver, css_selectors: List[str], timeout: int = DEFAULT_TIMEOUT_SECONDS):
    last_exc: Optional[Exception] = None
    for selector in css_selectors:
        try:
            element = WebDriverWait(driver, min(8, timeout)).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            return element
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
    # 最后再做一次统一的存在性等待，便于给出更清晰的报错
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css_selectors[0]))
        )
    except Exception as exc:  # noqa: BLE001
        last_exc = exc
    raise TimeoutException(f"未找到以下任一选择器: {css_selectors}. 最后错误: {last_exc}")


def safe_click(driver, element) -> None:
    try:
        element.click()
        return
    except Exception:
        pass
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.2)
        element.click()
        return
    except Exception:
        pass
    # 最后使用 JS 强制点击
    driver.execute_script("arguments[0].click();", element)


def accept_possible_alert(driver, max_wait_seconds: int = 10) -> bool:
    try:
        alert = WebDriverWait(driver, max_wait_seconds).until(EC.alert_is_present())
        text = alert.text
        logging.info("检测到浏览器原生弹窗，文本: %s", text)
        alert.accept()
        return True
    except TimeoutException:
        return False


def find_and_click_first(driver, css_selectors: List[str], timeout: int = DEFAULT_TIMEOUT_SECONDS) -> None:
    element = wait_for_any_and_return(driver, css_selectors, timeout=timeout)
    safe_click(driver, element)


def capture_artifacts_on_failure(driver, reason: str) -> None:
    try:
        base = pathlib.Path(__file__).resolve().with_name("bmc_collect_last")
        png_path = base.with_suffix(".png")
        html_path = base.with_suffix(".html")
        driver.save_screenshot(str(png_path))
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        logging.error("已保存调试信息到: %s, %s (原因: %s)", png_path, html_path, reason)
    except Exception as exc:  # noqa: BLE001
        logging.error("保存调试信息失败: %s", exc)


def perform_bmc_collection() -> None:
    driver = None
    try:
        logging.info("启动浏览器: %s (headless=%s)", BROWSER, HEADLESS)
        driver = create_webdriver()
        wait = WebDriverWait(driver, DEFAULT_TIMEOUT_SECONDS)

        logging.info("打开地址: %s", BMC_URL)
        driver.get(BMC_URL)

        # 登录
        username_input = wait_for_any_and_return(driver, SELECTORS["username"])  # 输入用户名
        username_input.clear()
        username_input.send_keys(BMC_USERNAME)

        password_input = wait_for_any_and_return(driver, SELECTORS["password"])  # 输入密码
        password_input.clear()
        password_input.send_keys(BMC_PASSWORD)

        find_and_click_first(driver, SELECTORS["login"])  # 点击登录

        # 可根据页面跳转情况做一次登录成功的简单判定/等待（视项目调整）
        time.sleep(1.0)

        # 点击“开始采集”按钮（div/button）
        logging.info("尝试点击采集按钮")
        find_and_click_first(driver, SELECTORS["collect"])

        # 处理可能出现的浏览器原生 confirm/alert
        if accept_possible_alert(driver, max_wait_seconds=8):
            logging.info("已确认原生弹窗")
        else:
            # 尝试 DOM 弹窗的确认按钮
            try:
                logging.info("未检测到原生弹窗，尝试点击 DOM 确认按钮")
                find_and_click_first(driver, SELECTORS["confirm"], timeout=15)
            except Exception:
                logging.info("未检测到 DOM 确认按钮，可能不需要确认")

        # 视需要，等待采集开始/状态提示（如有可选的状态元素可在此等待）
        time.sleep(2.0)
        logging.info("采集流程已触发，准备关闭浏览器")

    except Exception as exc:  # noqa: BLE001
        logging.exception("执行失败: %s", exc)
        if driver is not None:
            capture_artifacts_on_failure(driver, reason=str(exc))
        raise
    finally:
        if driver is not None:
            try:
                driver.quit()
            except WebDriverException:
                pass
        logging.info("浏览器已关闭")


def main() -> int:
    configure_logging()
    logging.info("BMC 自动采集脚本启动")
    logging.info("目标: %s", BMC_URL)
    try:
        perform_bmc_collection()
        logging.info("执行完成")
        return 0
    except Exception as exc:  # noqa: BLE001
        logging.error("执行出错: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main()) 