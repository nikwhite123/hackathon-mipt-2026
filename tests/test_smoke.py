import os
import time
import uuid

import pytest
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = os.getenv("E2E_BASE_URL", "http://127.0.0.1:8080")
SEEDED_ORG_CODE = os.getenv("E2E_ORG_CODE", "23")
HEADLESS = os.getenv("E2E_HEADLESS", "0") != "0"
TIMEOUT = int(os.getenv("E2E_TIMEOUT", "20"))
TEST_PASSWORD = os.getenv("E2E_TEST_PASSWORD", "Secret12345!")


def _make_driver() -> webdriver.Chrome:
    options = ChromeOptions()
    if HEADLESS:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1600,1200")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--lang=ru-RU")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


@pytest.fixture()
def driver():
    drv = _make_driver()
    yield drv
    drv.quit()


@pytest.fixture()
def wait(driver):
    return WebDriverWait(driver, TIMEOUT)


def unique_email() -> str:
    return f"selenium_{uuid.uuid4().hex[:10]}@example.com"


def open_app(driver):
    driver.get(BASE_URL)


def wait_text(wait, text: str):
    return wait.until(EC.visibility_of_element_located((By.XPATH, f"//*[contains(normalize-space(), '{text}')]")))


def wait_clickable(wait, by, value):
    return wait.until(EC.element_to_be_clickable((by, value)))


def visible_input_by_placeholder(driver, wait, placeholder: str):
    xpath = f"//input[@placeholder='{placeholder}' and not(contains(@style,'display: none'))]"
    return wait.until(EC.visibility_of_element_located((By.XPATH, xpath)))


def visible_password_input(wait):
    return wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@type='password']")))


def click_button_by_text(wait, text: str):
    xpath = (
        f"//button[normalize-space()='{text}']"
        f" | //button[.//*[normalize-space()='{text}']]"
        f" | //span[normalize-space()='{text}']/ancestor::button[1]"
    )
    return wait.until(EC.element_to_be_clickable((By.XPATH, xpath))).click()


def click_link_by_text(wait, text: str):
    xpath = f"//a[normalize-space()='{text}'] | //button[normalize-space()='{text}']"
    return wait.until(EC.element_to_be_clickable((By.XPATH, xpath))).click()


def ant_select_choose(driver, wait, label_text: str, option_text: str):
    label = wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, f"//label[normalize-space()='{label_text}']")
        )
    )
    form_item = label.find_element(By.XPATH, "./ancestor::div[contains(@class,'ant-form-item')][1]")
    selector = form_item.find_element(By.XPATH, ".//div[contains(@class,'ant-select-selector')]")
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", selector)
    selector.click()
    option_xpath = f"//div[contains(@class,'ant-select-item-option-content') and normalize-space()='{option_text}']"
    wait.until(EC.element_to_be_clickable((By.XPATH, option_xpath))).click()


def login_or_register_via_modal(driver, wait, email: str, password: str = TEST_PASSWORD, org_code: str = SEEDED_ORG_CODE):
    open_app(driver)
    click_button_by_text(wait, "Войти в систему")
    wait_text(wait, "Авторизация")
    click_link_by_text(wait, "Нет аккаунта? Создать")
    wait_text(wait, "Регистрация")

    visible_input_by_placeholder(driver, wait, "Email").send_keys(email)
    visible_password_input(wait).send_keys(password)
    visible_input_by_placeholder(driver, wait, "Имя").send_keys("Ivan")
    visible_input_by_placeholder(driver, wait, "Фамилия").send_keys("Petrov")
    visible_input_by_placeholder(driver, wait, "Код из приглашения").send_keys(org_code)

    click_button_by_text(wait, "Зарегистрироваться")
    wait_text(wait, "RT Infra Security")
    wait_text(wait, "Выйти")


def save_org_settings(driver, wait):
    click_link_by_text(wait, "Инфраструктура")
    wait_text(wait, "Настройка инфраструктуры")

    for tech in ["SQL", "Сеть"]:
        checkbox = wait.until(
            EC.element_to_be_clickable((By.XPATH, f"//label[.//span[normalize-space()='{tech}']]") )
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox)
        checkbox.click()

    click_button_by_text(wait, "Сохранить")
    wait_text(wait, "Настройки сохранены")
    wait_text(wait, "Уровень угрозы (Risk Score)")
    wait_text(wait, "Посмотреть меры защиты")


@pytest.mark.e2e
def test_public_landing_and_auth_modal(driver, wait):
    open_app(driver)
    wait_text(wait, "RT Infra")
    wait_text(wait, "Платформа аналитики ИБ")
    click_button_by_text(wait, "Войти в систему")
    wait_text(wait, "Авторизация")
    wait_text(wait, "Нет аккаунта? Создать")


@pytest.mark.e2e
def test_register_login_infrastructure_and_recommendations(driver, wait):
    email = unique_email()
    login_or_register_via_modal(driver, wait, email=email)
    wait_text(wait, "Дашборд")
    save_org_settings(driver, wait)


@pytest.mark.e2e
def test_navigation_to_audit_and_analytics(driver, wait):
    email = unique_email()
    login_or_register_via_modal(driver, wait, email=email)
    save_org_settings(driver, wait)

    click_link_by_text(wait, "Аудит")
    wait_text(wait, "Карта соответствия уязвимостей и угроз")
    wait.until(EC.presence_of_element_located((By.XPATH, "//table")))


@pytest.mark.e2e
def test_logout_returns_to_public_landing(driver, wait):
    email = unique_email()
    login_or_register_via_modal(driver, wait, email=email)
    click_button_by_text(wait, "Выйти")
    wait_text(wait, "Войти в систему")
    wait_text(wait, "Платформа аналитики ИБ")
