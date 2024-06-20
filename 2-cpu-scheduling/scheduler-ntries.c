/* Name: Daan Rosendal
 * Student number: 15229394
 * Study: Bachelor HBO-ICT (Software Engineering) at Windesheim in Zwolle. I follow Operating
 * Systems as a "bijvak".
 *
 * This file contains the first-come first-served scheduler with N-tries which tries to allocate N
 * next processes if an allocation fails.
 */

#include <stdio.h>
#include <stdlib.h>

#include "mem_alloc.h"
#include "schedule.h"

static long memory[MEM_SIZE];
int N_TRIES = 12;

// Dynamic array to hold the iterations of successful memory allocations inside N_TRIES loop
static int *success_iterations;
static int success_count = 0;
static int success_capacity = 10;

/* The scheduler function that schedules the processes */
static void cpu_scheduler() {}

/* This function moves a process from the new queue to the ready queue */
static void move_proc_to_ready_queue(student_pcb *proc, int index) {
    proc->mem_base = index;
    queue_remove(&new_proc, proc);
    queue_append(&ready_proc, proc);
}

/* This function tries to allocate memory and uses a loop to try N_TRIES times if the allocation
 * fails */
static void give_memory() {
    int index;
    student_pcb *proc;

    proc = new_proc;
    if (proc) {
        index = mem_get(proc->mem_need);
        if (index >= 0) {
            move_proc_to_ready_queue(proc, index);
        } else {
            // Only start recording successes in this loop
            for (int i = 0; i < N_TRIES; i++) {
                proc = proc->next;
                if (!proc)
                    break;
                index = mem_get(proc->mem_need);
                if (index >= 0) {
                    move_proc_to_ready_queue(proc, index);
                    if (success_count == success_capacity) {
                        success_capacity *= 2;
                        success_iterations =
                            realloc(success_iterations, sizeof(int) * success_capacity);
                    }
                    success_iterations[success_count++] = i + 1; // Record the iteration of success
                    break;
                }
            }
        }
    }
}

/* This function reclaims memory from defunct processes */
static void reclaim_memory() {
    student_pcb *proc;
    proc = defunct_proc;
    while (proc) {
        if (proc->userdata) {
            free(proc->userdata);
        }
        mem_free(proc->mem_base);
        proc->mem_base = -1;
        rm_process(&proc);
        proc = defunct_proc;
    }
}

/* This function compares two integers */
int compare_int(const void *a, const void *b) { return (*(int *)a - *(int *)b); }

/* Helper function to calculate statistics */
static void calculate_statistics(int *success_iterations, int success_count) {
    qsort(success_iterations, success_count, sizeof(int), compare_int);
    int median = success_iterations[success_count / 2];
    int max = success_iterations[success_count - 1];
    double average = 0;
    for (int i = 0; i < success_count; i++) {
        average += success_iterations[i];
    }
    average /= success_count;

    printf("Statistics of memory allocation successes within N_TRIES loop:\n");
    printf("Average iteration: %.2f\n", average);
    printf("Median iteration: %d\n", median);
    printf("Maximum iteration: %d\n", max);
}

/* Helper function to print frequencies */
static void print_frequencies(int *frequency, int max) {
    printf("Successes per iteration number up to the maximum successful iteration:\n");
    for (int i = 1; i <= max; i++) {
        if (frequency[i] > 0) {
            printf("Iteration %d: %d successes\n", i, frequency[i]);
        }
    }
}

/* Helper function to calculate frequencies */
static int *calculate_frequencies(int *success_iterations, int success_count, int max) {
    int *frequency = calloc(max + 1, sizeof(int));
    if (frequency == NULL) {
        printf("Memory allocation failed for frequency array.\n");
        return NULL;
    }
    for (int i = 0; i < success_count; i++) {
        frequency[success_iterations[i]]++;
    }
    return frequency;
}

/* The main function that orchestrates the final calculations */
static void my_finale() {
    if (success_count == 0) {
        printf("No successful memory allocations recorded within N_TRIES loop.\n");
        return;
    }

    calculate_statistics(success_iterations, success_count);
    int max = success_iterations[success_count - 1];
    int *frequency = calculate_frequencies(success_iterations, success_count, max);

    if (frequency) {
        print_frequencies(frequency, max);
        free(frequency);
    }

    free(success_iterations); // Free the dynamic array
}

/* Initialize the memory and set the finale function */
static void initialise() {
    mem_init(memory);
    finale = my_finale;
    success_iterations = malloc(sizeof(int) * success_capacity);

    // ask for the number of tries with scanf, if the input is invalid, ask again
    while (N_TRIES <= 0) {
        printf("Enter a positive integer value for N-tries: ");

        if (scanf("%d", &N_TRIES) != 1) {
            printf("Invalid input. Please enter a positive integer.\n");
            while (getchar() != '\n')
                ;
        }
    }
}

/* This function is responsible for calling the correct function based on the event */
void schedule(event_type event) {
    static int first = 1;
    if (first) {
        initialise();
        first = 0;
    }

    switch (event) {
    case NEW_PROCESS_EVENT:
        give_memory();
        break;
    case TIME_EVENT:
    case IO_EVENT:
        cpu_scheduler();
        break;
    case READY_EVENT:
        break;
    case FINISH_EVENT:
        reclaim_memory();
        give_memory();
        cpu_scheduler();
        break;
    default:
        printf("I cannot handle event nr. %d\n", event);
        break;
    }
}
