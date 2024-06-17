import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

class TestPruebaautocorrelacion():
    def setup_method(self, method):
        chromedriver_path = "C:/Users/carlo/Desktop/djangoproject/drivers/chromedriver.exe"
        service = Service(chromedriver_path)
        self.driver = webdriver.Chrome(service=service)
        self.vars = {}

    def teardown_method(self, method):
        self.driver.quit()

    def test_pruebaautocorrelacion(self):
        self.setup_method(None)
        self.driver.get("http://127.0.0.1:8000/")
        self.driver.set_window_size(1936, 1048)
        time.sleep(1)
        self.driver.find_element(By.LINK_TEXT, "Ingresar").click()
        self.driver.find_element(By.ID, "id_username").send_keys("admin")
        self.driver.find_element(By.ID, "id_password").click()
        self.driver.find_element(By.ID, "id_password").send_keys("admin")
        self.driver.find_element(By.CSS_SELECTOR, ".btn").click()
        self.driver.find_element(By.LINK_TEXT, "Analizar").click()
        time.sleep(1)
        self.driver.find_element(By.ID, "id_nombre").click()
        self.driver.find_element(By.ID, "id_nombre").send_keys("prueba test selenium")
        self.driver.find_element(By.ID, "id_descripcion").click()
        self.driver.find_element(By.ID, "id_descripcion").send_keys("esto es una prueba de test")
        self.driver.find_element(By.ID, "id_tipos_de_dato_1").click()
        self.driver.find_element(By.ID, "id_tipos_de_dato_2").click()
        scroll_script = "window.scrollTo(0, document.body.scrollHeight);"
        self.driver.execute_script(scroll_script)
        time.sleep(1)
        self.driver.find_element(By.ID, "id_terminos_aceptados").click()
        self.driver.find_element(By.CSS_SELECTOR, ".btn").click()
        click_en_nombre = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "prueba test selenium"))
        )
        click_en_nombre.click()
        time.sleep(1)
        imagen = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".cuadro:nth-child(1) img"))
        )
        self.driver.execute_script("arguments[0].scrollIntoView(true);", imagen)
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".cuadro:nth-child(1) img"))).click()
        self.driver.find_element(By.ID, "id_titulo").click()
        self.driver.find_element(By.ID, "id_titulo").send_keys("prueba")
        self.driver.find_element(By.ID, "id_lag").click()
        self.driver.find_element(By.ID, "id_lag").send_keys("15")
        self.driver.find_element(By.ID, "id_tipo").click()
        dropdown = self.driver.find_element(By.ID, "id_tipo")
        dropdown.find_element(By.XPATH, "//option[. = 'Parcial']").click()
        self.driver.find_element(By.ID, "id_metodo").click()
        dropdown = self.driver.find_element(By.ID, "id_metodo")
        dropdown.find_element(By.XPATH, "//option[. = 'Pearson']").click()
        self.driver.find_element(By.ID, "id_visualizacion").click()
        self.driver.find_element(By.ID, "id_mostrar_datos").click()
        dropdown = self.driver.find_element(By.ID, "id_mostrar_datos")
        dropdown.find_element(By.XPATH, "//option[. = 'Consumo']").click()
        self.driver.find_element(By.NAME, "action").click()
        self.driver.execute_script(scroll_script)
        time.sleep(2)
        self.driver.find_element(By.XPATH, "(//button[@type=\'button\'])[3]").click()
        time.sleep(1)
        self.driver.find_element(By.XPATH, "//button[contains(text(), 'Guardar')]").click()
        time.sleep(1)
        self.driver.find_element(By.LINK_TEXT, "Consultar resultados").click()
        time.sleep(1)
        self.driver.find_element(By.ID, "id_titulo").click()
        self.driver.find_element(By.ID, "id_titulo").send_keys("prueba")
        self.driver.find_element(By.CSS_SELECTOR, ".btn-danger").click()
        time.sleep(1)
        self.driver.find_element(By.LINK_TEXT, "Volver").click()
        time.sleep(1)
        self.driver.find_element(By.LINK_TEXT, "Volver").click()
        time.sleep(1)
        self.driver.find_element(By.LINK_TEXT, "Volver").click()
        time.sleep(1)
        self.driver.find_element(By.NAME, "analisis_uuids").click()
        self.driver.find_element(By.ID, "delete-selected").click()

if __name__ == "__main__":
    test = TestPruebaautocorrelacion()
    test.test_pruebaautocorrelacion()
