#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <time.h>
#include <unistd.h>
#include "vl53l5cx_api.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/uart.h"
#include "string.h"
#include "esp_system.h"
#include "driver/gpio.h" // Make sure to include the GPIO driver for manipulating pins

#define TXD_PIN (20)
#define RXD_PIN (21)
#define NEW_I2C_ADDRESS ((uint16_t)0x30 << 1) // Shift left to account for 7-bit address format

void delay_500ms() {
    const TickType_t xDelay = pdMS_TO_TICKS(500); // Convert 500ms to ticks
    vTaskDelay(xDelay); // Delay for 500ms (in ticks)
}

void init_uart() {
    const uart_config_t uart_config = {
        .baud_rate = 115200,
        .data_bits = UART_DATA_8_BITS,
        .parity = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
        .source_clk = UART_SCLK_APB,
    };
    // Install UART driver, and get the queue.
    uart_driver_install(UART_NUM_1, 1024 * 2, 0, 0, NULL, 0);
    // Configure UART parameters
    uart_param_config(UART_NUM_1, &uart_config);
    uart_set_pin(UART_NUM_1, TXD_PIN, RXD_PIN, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE);
}

void app_main(void) {

    init_uart();
    // Define the i2c bus configuration
    i2c_port_t i2c_port = I2C_NUM_1;
    i2c_config_t i2c_config = {
        .mode = I2C_MODE_MASTER,
        .sda_io_num = 6,
        .scl_io_num = 7,
        .sda_pullup_en = GPIO_PULLUP_ENABLE,
        .scl_pullup_en = GPIO_PULLUP_ENABLE,
        .master.clk_speed = VL53L5CX_MAX_CLK_SPEED,
    };
    
    gpio_set_direction(GPIO_NUM_0, GPIO_MODE_OUTPUT);
    gpio_set_direction(GPIO_NUM_1, GPIO_MODE_OUTPUT);
    gpio_set_level(GPIO_NUM_0, 1);
    gpio_set_level(GPIO_NUM_1, 1);

    delay_500ms();
    

    i2c_param_config(i2c_port, &i2c_config);
    i2c_driver_install(i2c_port, i2c_config.mode, 0, 0, 0);

    uint8_t 				status, loop, isAlive, isReady, i;
    VL53L5CX_Configuration Dev, Dev2; // Sensor configuration
    VL53L5CX_ResultsData 	Results, Results2;


    // Initialize the first sensor (Dev)
    Dev.platform.address = VL53L5CX_DEFAULT_I2C_ADDRESS;
    Dev.platform.port = i2c_port;

    // Init first sensor
    status = vl53l5cx_init(&Dev);
    if (status) {
        printf("VL53L5CX ULD Loading failed for first sensor %d\n", Dev.platform.address);
        return;
    }

    // Check if the first sensor is alive
    status = vl53l5cx_is_alive(&Dev, &isAlive);
    if (!isAlive || status) {
        printf("First VL53L5CX not detected at requested address %d: \n", Dev.platform.address);
        return;}
    
    // Initialize the second sensor (Dev2) and change its I2C address
    Dev2.platform.address = VL53L5CX_DEFAULT_I2C_ADDRESS;
    Dev2.platform.port = i2c_port;

    // Disable other device
    gpio_set_level(GPIO_NUM_0, 0);
    // Change the I2C address of the second sensor
    vl53l5cx_set_i2c_address(&Dev2, NEW_I2C_ADDRESS);
    delay_500ms();
    // Re-enable other device
    gpio_set_level(GPIO_NUM_0, 1);
    
    // Initialize the second sensor with the new address
    status = vl53l5cx_init(&Dev2);
    if (status) {
        printf("VL53L5CX ULD Loading failed for second sensor %d\n", Dev2.platform.address);
        return;
    }

    // Check if the second sensor is alive (now at the new I2C address)
    status = vl53l5cx_is_alive(&Dev2, &isAlive);
    if (!isAlive || status) {
        printf("Second VL53L5CX not detected at the new I2C address %d: \n", Dev2.platform.address);
        return;
    }

    vl53l5cx_set_resolution(&Dev,VL53L5CX_RESOLUTION_8X8);
    vl53l5cx_set_resolution(&Dev2,VL53L5CX_RESOLUTION_8X8);

    printf("Both VL53L5CX ULD ready! Sensor1: %d Sensor2: %d (Version: %s)\n",Dev.platform.address,Dev2.platform.address, VL53L5CX_API_REVISION);
    
    // Start ranging for both sensors
    status = vl53l5cx_start_ranging(&Dev);
    if(status) {
        printf("Failed to start ranging on the first sensor\n");
        return;
    }

    status = vl53l5cx_start_ranging(&Dev2);
    if(status) {
        printf("Failed to start ranging on the second sensor\n");
        return;
    }

    loop = 0;
    char uart_buffer[1024];
    while(loop < 10) {
        // Fetching and sending data for the first sensor
        status = vl53l5cx_check_data_ready(&Dev, &isReady);
        if(isReady) {
            vl53l5cx_get_ranging_data(&Dev, &Results);

            // Send each distance measurement in a separate chunk
            for(i = 0; i < 64; i++) {
                snprintf(uart_buffer, sizeof(uart_buffer), "A%d;", Results.distance_mm[i]);
                uart_write_bytes(UART_NUM_1, uart_buffer, strlen(uart_buffer));
                vTaskDelay(pdMS_TO_TICKS(10)); // Small delay between chunks
            }
        }

        // Fetching and sending data for the second sensor
        status = vl53l5cx_check_data_ready(&Dev2, &isReady);
        if(isReady) {
            vl53l5cx_get_ranging_data(&Dev2, &Results2);

            // Send each distance measurement in a separate chunk
            for(i = 0; i < 64; i++) {
                snprintf(uart_buffer, sizeof(uart_buffer), "B%d;", Results2.distance_mm[i]);
                uart_write_bytes(UART_NUM_1, uart_buffer, strlen(uart_buffer));
                vTaskDelay(pdMS_TO_TICKS(10)); // Small delay between chunks
            }
        }

        // Wait a bit before fetching new data to avoid too high polling
        WaitMs(&(Dev.platform), 10);
        WaitMs(&(Dev2.platform), 10);

        loop++;
    }


    status = vl53l5cx_stop_ranging(&Dev);
    if(status) {
        printf("Failed to stop ranging on the first sensor\n");
    }

    status = vl53l5cx_stop_ranging(&Dev2);
    if(status) {
        printf("Failed to stop ranging on the second sensor\n");
    }

    printf("End of ULD demo for both sensors\n");

}