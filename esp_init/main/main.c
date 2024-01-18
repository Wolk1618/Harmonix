
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

void app_main(void)
{
    
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

    uint8_t 				status, loop, isAlive, isReady, i;
    VL53L5CX_Configuration 	Dev, Dev2;			/* Sensor configuration */
    
    Dev.platform.address = VL53L5CX_DEFAULT_I2C_ADDRESS;
    Dev.platform.port = i2c_port;

    // Initialize the second sensor (Dev2) with a new address
    //Dev2.platform.address = VL53L5CX_DEFAULT_I2C_ADDRESS; // Temporarily use default address for initialization
    Dev2.platform.port = i2c_port;

    uint16_t new_address2 = 0x20; // New I2C address for Dev2
    //vl53l5cx_set_i2c_address(&Dev2, new_address2);
    
    Dev2.platform.address = new_address2; // Update the address in the device configuration


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


}