# E-Commerce Product & Restock Monitor

`Python` `Selenium` `Distributed-Systems` `Networking` `Web-Scraping`

An automated monitoring bot based on distributed systems and networking principles, designed to track new products and restock status across multiple e-commerce platforms (Kakao, SSF, Gentle Monster) in real-time.

## 1\. Project Overview

This project is not a simple scraping script, but rather a monitoring system that treats multiple independent websites as **Distributed Targets** and continuously tracks their state (new products, stock status).

The `main.py` acts as a **Coordinator**, while the `crawler` modules function as **Workers** to periodically collect data. The collected data is then sent to an external notification system (Discord) and an internal database (Excel/JSON), forming a complete **Data Pipeline**.

## 2\. System Architecture

This system follows a distributed structure where multiple services communicate organically.

1.  **Coordinator (`main.py`):**

      * The main process that schedules and manages all tasks.
      * Loads system-wide settings from `config.json`, such as the proxy list and task cycle frequency (`wait_time`).
      * Triggers the tasks for each `Worker` via a periodic `while` loop.

2.  **Workers (`kakao_crawler.py`, `ssf_crawler.py`, ...):**

      * Data collection modules specialized for each target website.
      * Receive task commands from the `Coordinator` and communicate with target servers via the `Network Manager`.
      * Perform HTML parsing, data refinement, and state comparison (new product/restock) logic.

3.  **Network Manager (`web_driver_manager.py`):**

      * A core service that abstracts and manages all **L7 (HTTP/HTTPS) network communication**.
      * Manages the lifecycle of Selenium WebDriver instances.
      * Dynamically handles **network proxy setup and authentication**.
      * Manages supplementary HTTP requests, such as image downloads using `requests`.

4.  **State Manager (JSON Files):**

      * Uses `latest_item_info.json` and `restock_check_list.json` files as **Persistent State Storage**.
      * Enables **Checkpointing** by recording the last-seen item, which prevents duplicate data collection and allows the system to resume from its previous state upon restart.

5.  **External Services (APIs):**

      * **Target Servers (Kakao, SSF):** The remote servers from which data is collected.
      * **Discord Webhook API:** An external notification system to which refined data is sent **asynchronously**.

-----

## 3\. Highlights

### 1. Network Communication & Proxy Management

  * **HTTP/S Communication:** Performs L7 communication with target servers using Selenium WebDriver and the `requests` library.
  * **Dynamic Proxy Authentication:** `web_driver_manager.py` goes beyond simple proxy use; it **dynamically generates a `proxy_auth_plugin.zip` file** on the fly for proxies requiring `username`:`password` authentication. This demonstrates the ability to solve complex authentication and routing problems in varied network environments.
  * **Proxy Rotation:** `main.py` rotates through a list of proxies (`pop(0)`, `append(curr)`) to **bypass IP-based Rate Limiting** and ensure the anonymity of the monitoring nodes.

### 2. API Integration & Data Pipelining

  * **REST API Integration:** Utilizes the `discord-webhook` library to send refined data to a Discord Webhook URL (an HTTP POST Endpoint). This showcases experience in **API-based integration between disparate systems**.
  * **Data Serialization:** Serializes collected data into Excel (via `pandas`) and state data into `json` (serialization/deserialization) to **persist the system's state**.

### 3. Network Resilience & Error Handling

  * **Robust Element Search:** The `get_element(s)` functions in `web_driver_manager.py` include logic to **automatically refresh the page and retry** if a `NoSuchElementException` occurs.
  * **Timeouts and Retries:** The `get_page` function **retries up to 10 times** on a page load failure. The `download_image` function **recursively retries** if a download fails or the resulting file size is anomalous. This is a key logic for ensuring **task stability and data integrity** in unstable network conditions.

### 4. System Monitoring & Logging

  * **Resource Monitoring:** `resource_monitor_manager.py` uses `psutil` to track the **RAM usage** of the current process (by PID). This is essential for **Health Checks** and resource management in a distributed system.
  * **Custom Logging:** A dedicated `log_manager.py` separates log levels (DEBUG, INFO, ERROR), enabling **rapid troubleshooting** and root cause analysis when a system failure occurs.

-----

## 4\. Tech Stack

  * **Core:** Python
  * **Web Automation & Networking:** Selenium, requests
  * **Data Handling:** Pandas, JSON
  * **System Monitoring:** psutil
  * **Notifications:** discord-webhook
