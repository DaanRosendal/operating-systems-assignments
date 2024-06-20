/* Name: Daan Rosendal
 * Student number: 15229394
 * Study: Bachelor HBO-ICT (Software Engineering) at Windesheim in Zwolle. I follow Operating
 * Systems as a "bijvak".
 *
 * This file contains the round-robin scheduler, which is a scheduler that schedules processes by
 * giving each process a time slice in a circular order.
 */

#include <stdio.h>
#include <stdlib.h>

#include "mem_alloc.h"
#include "schedule.h"
#include <stdbool.h>

static long memory[MEM_SIZE];
const int N_TRIES = 12;
static double time_slice = 1;

/* The scheduler function that schedules the processes */
static void cpu_scheduler() { set_slice(time_slice); }

static void round_robin() {
    student_pcb *proc;

    proc = ready_proc;
    if (proc) {
        queue_remove(&ready_proc, proc);
        queue_append(&ready_proc, proc);
    }
}

/* This function moves a process from the new queue to the ready queue */
static void move_proc_to_ready_queue(student_pcb *proc, int index) {
    proc->mem_base = index;

    queue_remove(&new_proc, proc);
    queue_append(&ready_proc, proc);
}

/* The high-level memory allocation scheduler is implemented here */
static void give_memory() {
    int index;
    student_pcb *proc;

    proc = new_proc;
    if (proc) {
        index = mem_get(proc->mem_need);

        if (index >= 0) {
            move_proc_to_ready_queue(proc, index);
        } else {
            for (int i = 0; i < N_TRIES; i++) {
                proc = proc->next;
                if (!proc) {
                    break;
                }

                index = mem_get(proc->mem_need);

                if (index >= 0) {
                    move_proc_to_ready_queue(proc, index);
                }
            }
        }
    }
}

/* Here we reclaim the memory of a process after it
  has finished */
static void reclaim_memory() {
    student_pcb *proc;

    proc = defunct_proc;
    while (proc) {
        /* Free your own administrative structure if it exists
         */
        if (proc->userdata) {
            free(proc->userdata);
        }
        /* Free the simulated allocated memory
         */
        mem_free(proc->mem_base);
        proc->mem_base = -1;

        /* Call the function that cleans up the simulated process
         */
        rm_process(&proc);

        /* See if there are more processes to be removed
         */
        proc = defunct_proc;
    }
}

/* This function is called when the simulation is finished */
static void my_finale() {}

/* Initialise the memory and set the finale function */
void initialise() {
    mem_init(memory);
    finale = my_finale;

    // ask for the time slice with scanf, if the input is invalid, ask again
    while (true) {
        printf("Enter your desired time slice (in ms): ");
        if (time_slice > 0) {
            printf("Current time slice is %.2f ms\n", time_slice);
            break;
        } else {
            printf("Current time slice is not set\n");
        }

        if (scanf("%lf", &time_slice) == 1) {
            break;
        } else {
            printf("Invalid input. Please enter a number.\n");
            while (getchar() != '\n') {
            }
        }
    }
}

/* The main scheduling routine */
void schedule(event_type event) {
    static int first = 1;

    if (first) {
        initialise();
        first = 0;
    }

    switch (event) {
    case NEW_PROCESS_EVENT:
        give_memory();
        cpu_scheduler();
        break;
    case TIME_EVENT:
        round_robin();
        cpu_scheduler();
        break;
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
