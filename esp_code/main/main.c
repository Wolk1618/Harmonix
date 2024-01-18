
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

#define TXD_PIN (20)
#define RXD_PIN (21)

#define VL53L5CX_DEFAULT_I2C_ADDRESS1 ((uint16_t)0x52)

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

void printDistanceResults(const VL53L5CX_ResultsData *Results) {
    printf("Distance values (mm): ");
    for (int i = 0; i < 16; i++) {
        printf("%d ", Results->distance_mm[i]);
    }
    printf("\n");
}

void app_main(void)
{
    init_uart();
    
    //Define the i2c bus configuration
    i2c_port_t i2c_port = I2C_NUM_1;
    i2c_config_t i2c_config = {
            .mode = I2C_MODE_MASTER,
            .sda_io_num = 6,
            .scl_io_num = 7,
            .sda_pullup_en = GPIO_PULLUP_ENABLE,
            .scl_pullup_en = GPIO_PULLUP_ENABLE,
            .master.clk_speed = VL53L5CX_MAX_CLK_SPEED,
    };

    i2c_param_config(i2c_port, &i2c_config);
    i2c_driver_install(i2c_port, i2c_config.mode, 0, 0, 0);

    /*********************************/
    /*   VL53L5CX ranging variables  */
    /*********************************/

    uint8_t 				status, loop, isAlive, isReady, i;
    VL53L5CX_Configuration 	Dev, Dev2;			/* Sensor configuration */
    VL53L5CX_ResultsData 	Results, Results2;		/* Results data from VL53L5CX */
    
    Dev.platform.address = VL53L5CX_DEFAULT_I2C_ADDRESS;
    Dev.platform.port = i2c_port;

    // Initialize the second sensor (Dev2) with a new address
    //Dev2.platform.address = VL53L5CX_DEFAULT_I2C_ADDRESS; // Temporarily use default address for initialization

    Dev2.platform.port = i2c_port;
    uint16_t new_address2 = 0x20; // New I2C address for Dev2
    //vl53l5cx_set_i2c_address(&Dev2, new_address2);
    Dev2.platform.address = new_address2; // Update the address in the device configuration
    
    /* (Optional) Reset sensor toggling PINs (see platform, not in API) */
    //Reset_Sensor(&(Dev.platform));

    /* (Optional) Set a new I2C address if the wanted address is different
    * from the default one (filled with 0x20 for this example).
    */


    /*********************************/
    /*   Power on sensor and init    */
    /*********************************/

    /* (Optional) Check if there is a VL53L5CX sensor connected */
    status = vl53l5cx_is_alive(&Dev, &isAlive);
    if(!isAlive || status)
    {
        printf("VL53L5CX not detected at requested address\n");
        return;
    }

    /* (Mandatory) Init first sensor */
    status = vl53l5cx_init(&Dev);
    if(status)
    {
        printf("VL53L5CX ULD Loading failed\n");
        return;
    }

    // Initialize the second sensor
    status = vl53l5cx_is_alive(&Dev2, &isAlive);
    if(!isAlive || status) {
        printf("Second VL53L5CX not detected at requested address\n");
        return;
    }

    status = vl53l5cx_init(&Dev2);
    if(status) {
        printf("Second VL53L5CX ULD Loading failed\n");
        return;
    }

    printf("Both VL53L5CX ULD ready ! (Version : %s)\n",
           VL53L5CX_API_REVISION);


    /*********************************/
    /*         Ranging loop          */
    /*********************************/

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
    while(loop < 4) {

        printf("Batch number : %d\n", loop);
        char uart_buffer[256];
        char stringData[1000];
        char bufferString[10];

        // Fetching data for the first sensor
        status = vl53l5cx_check_data_ready(&Dev, &isReady);
        if(isReady) {
            vl53l5cx_get_ranging_data(&Dev, &Results);
        }

        // Fetching data for the second sensor
        status = vl53l5cx_check_data_ready(&Dev2, &isReady);
        if(isReady) {
            vl53l5cx_get_ranging_data(&Dev2, &Results2);
        }

        // Formatting data from first sensor and concatenating it on one string
        for(i = 0; i < 16; i++)
        {
            snprintf(bufferString, sizeof(bufferString), "%d", Results.distance_mm[i]);
            strcat(stringData, bufferString);
            strcat(stringData, "; ");
        }
        strcat(stringData, " - ");

        // Formatting data from second sensor and concatenating it on one string
        for(i = 0; i < 16; i++)
        {
            snprintf(bufferString, sizeof(bufferString), "%d", Results2.distance_mm[i]);
            strcat(stringData, bufferString);
            strcat(stringData, "; ");
        }
        strcat(stringData, "\n");

        // Send the formatted string over UART
        snprintf(uart_buffer, sizeof(uart_buffer), stringData, i, Results.distance_mm[VL53L5CX_NB_TARGET_PER_ZONE*i]);
        uart_write_bytes(UART_NUM_1, uart_buffer, strlen(uart_buffer));            
            
        // Wait a few ms to avoid too high polling
        WaitMs(&(Dev.platform), 5);
        WaitMs(&(Dev2.platform), 5);

        loop++;
    }

    status = vl53l5cx_stop_ranging(&Dev);
    if(status) {
        printf("Failed to stop ranging on the first sensor\n");
    }

    status = vl53l5cx_stop_ranging(&Dev2);
    if(status) {
        printf("Failed to ranging on the second sensor\n");
    }

    printf("End of ULD demo for both sensors\n");
}