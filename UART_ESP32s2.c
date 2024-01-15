#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/uart.h"
#include "string.h"

#define TXD_PIN (20)
#define RXD_PIN (21)

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
    const char *message = "Hello World\n";  // Newline added to mark the end of the message

    while (1) {
        // Send the message
        uart_write_bytes(UART_NUM_1, message, strlen(message));
        // Delay for 2 seconds
        vTaskDelay(pdMS_TO_TICKS(2000));
    }
}
