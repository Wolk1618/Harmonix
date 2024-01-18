
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include "vl53l5cx_api.h"

void app_main(void){
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

    uint16_t new_address2 = 0x20; // New I2C address for Dev2
    //vl53l5cx_set_i2c_address(&Dev2, new_address2);
    Dev2.platform.address = new_address2; // Update the address in the device configuration
    Dev2.platform.port = i2c_port;
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

    /* (Mandatory) Init VL53L5CX sensor */
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
    while(loop < 10) {
        // Check data ready for the first sensor
        status = vl53l5cx_check_data_ready(&Dev, &isReady);
        if(isReady) {
            vl53l5cx_get_ranging_data(&Dev, &Results);
            printf("First sensor data no: %3u\n", Dev.streamcount);
            for(i = 0; i < 16; i++) {
                printf("Zone: %3d, Status: %3u, Distance: %4d mm\n",
                       i,
                       Results.target_status[VL53L5CX_NB_TARGET_PER_ZONE * i],
                       Results.distance_mm[VL53L5CX_NB_TARGET_PER_ZONE * i]);
            }
            printf("\n");
        }

        // Check data ready for the second sensor
        status = vl53l5cx_check_data_ready(&Dev2, &isReady);
        if(isReady) {
            vl53l5cx_get_ranging_data(&Dev2, &Results2);
            printf("Second sensor data no: %3u\n", Dev2.streamcount);
            for(i = 0; i < 16; i++) {
                printf("Zone: %3d, Status: %3u, Distance: %4d mm\n",
                       i,
                       Results2.target_status[VL53L5CX_NB_TARGET_PER_ZONE * i],
                       Results2.distance_mm[VL53L5CX_NB_TARGET_PER_ZONE * i]);
            }
            printf("\n");
        }

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