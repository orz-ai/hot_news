import threading
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from app.utils.logger import log

class BrowserManager:
    """浏览器管理器，提供共享的Chrome浏览器实例"""
    _instance = None
    _lock = threading.Lock()
    _driver = None
    _driver_path = None
    _last_activity = 0
    _max_idle_time = 1800  # 最大空闲时间（秒），默认30分钟
    
    def __new__(cls, *args, **kwargs):
        """单例模式实现"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(BrowserManager, cls).__new__(cls)
                    cls._instance._init_driver_path()
                    cls._instance._start_idle_monitor()
        return cls._instance
    
    def _init_driver_path(self):
        """初始化ChromeDriver路径"""
        try:
            self._driver_path = ChromeDriverManager().install()
            log.info(f"ChromeDriver已安装: {self._driver_path}")
        except Exception as e:
            log.error(f"ChromeDriver安装失败: {str(e)}")
            raise
    
    def _start_idle_monitor(self):
        """启动空闲监控线程"""
        def monitor():
            while True:
                time.sleep(60)  # 每分钟检查一次
                try:
                    with self._lock:
                        if self._driver is not None:
                            current_time = time.time()
                            if current_time - self._last_activity > self._max_idle_time:
                                log.info(f"浏览器空闲超过{self._max_idle_time}秒，释放资源")
                                self._quit_driver()
                except Exception as e:
                    log.error(f"浏览器监控线程异常: {str(e)}")
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
        log.info("浏览器空闲监控线程已启动")
    
    def get_driver(self):
        """获取Chrome浏览器实例"""
        with self._lock:
            self._last_activity = time.time()
            if self._driver is None:
                self._create_driver()
            return self._driver
    
    def _create_driver(self):
        """创建新的Chrome浏览器实例"""
        log.info("创建新的Chrome浏览器实例")
        options = webdriver.ChromeOptions()
        # 基本配置（无头模式）
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        # 内存优化配置
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-application-cache")
        options.add_argument("--js-flags=--expose-gc")
        options.add_argument("--memory-pressure-off")
        options.add_argument("--disable-default-apps")
        # 日志级别
        options.add_argument("--log-level=3")
        
        self._driver = webdriver.Chrome(
            service=Service(self._driver_path), 
            options=options
        )
        self._driver.set_page_load_timeout(30)
        
    def _quit_driver(self):
        """关闭浏览器实例"""
        if self._driver:
            try:
                self._driver.quit()
                log.info("浏览器实例已关闭")
            except Exception as e:
                log.error(f"关闭浏览器实例出错: {str(e)}")
            finally:
                self._driver = None
    
    def release_driver(self):
        """使用完毕后标记为活动状态"""
        with self._lock:
            self._last_activity = time.time()
    
    def get_page_content(self, url, wait_time=5):
        """获取指定URL的页面内容，并自动处理浏览器"""
        driver = self.get_driver()
        try:
            driver.get(url)
            time.sleep(wait_time)  # 等待页面加载
            page_source = driver.page_source
            self.release_driver()
            return page_source, driver
        except Exception as e:
            log.error(f"获取页面内容失败: {str(e)}")
            self.release_driver()
            raise
    
    def shutdown(self):
        """关闭浏览器管理器"""
        with self._lock:
            self._quit_driver() 