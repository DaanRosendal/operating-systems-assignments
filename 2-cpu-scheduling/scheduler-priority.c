/* Name: Daan Rosendal
 * Student number: 15229394
 * Study: Bachelor HBO-ICT (Software Engineering) at Windesheim in Zwolle. I follow Operating
 * Systems as a "bijvak".
 *
 * This file contains the priority scheduler, which is my advanced scheduler that has improved
 * performance over the round-robin scheduler.
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include "mem_alloc.h"
#include "schedule.h"

static long memory[MEM_SIZE];
const int N_TRIES = 12;

int AGING_TIME_INTERVAL;
int AGING_FACTOR;

/* Comparator function for process priorities */
int compare_prio(const void *a, const void *b) {
    student_pcb *proc_a = *(student_pcb **)a;
    student_pcb *proc_b = *(student_pcb **)b;

    priority_level priority_a = ((userdata_t *)proc_a->userdata)->priority;
    priority_level priority_b = ((userdata_t *)proc_b->userdata)->priority;

    priority_a -= ((userdata_t *)proc_a->userdata)->age;
    priority_b -= ((userdata_t *)proc_b->userdata)->age;

    // if priority is less than 0 then set it to 0
    if (priority_a < 0) {
        priority_a = 0;
    }

    if (priority_b < 0) {
        priority_b = 0;
    }

    return priority_a - priority_b;
}

/* Prepend the process with the highest priority to the ready queue */
static void prepend_highest_prio_proc() {
    if (!ready_proc) {
        return;
    }

    student_pcb *proc = ready_proc;
    student_pcb *highest_prio_proc = proc;
    while (proc) {
        if (compare_prio(&proc, &highest_prio_proc) < 0) {
            highest_prio_proc = proc;
        }
        proc = proc->next;
    }

    queue_remove(&ready_proc, highest_prio_proc);
    queue_prepend(&ready_proc, highest_prio_proc);
}

/* The scheduler function that schedules the processes */
static void cpu_scheduler() {
    prepend_highest_prio_proc();

    set_slice(AGING_TIME_INTERVAL);
}

/* Move the process to the ready queue */
static void move_proc_to_ready_queue(student_pcb *proc, int index) {
    proc->mem_base = index;

    double relative_mem_need = (double)proc->mem_need / MEM_SIZE;

    userdata_t *userdata = (userdata_t *)malloc(sizeof(userdata_t));
    userdata->age = 0;
    userdata->priority = (priority_level)(relative_mem_need * 20);
    proc->userdata = userdata;

    queue_remove(&new_proc, proc);
    queue_append(&ready_proc, proc);
}

/* Increase the age of all processes in the ready queue */
void increase_age() {
    student_pcb *proc = ready_proc;

    if (proc) {
        proc = proc->next;
    }

    while (proc) {
        ((userdata_t *)proc->userdata)->age += AGING_FACTOR;
        proc = proc->next;
    }
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
        if (proc->userdata) {
            free(proc->userdata);
        }
        mem_free(proc->mem_base);
        proc->mem_base = -1;
        rm_process(&proc);
        proc = defunct_proc;
    }
}

/* The final function that is called when the simulation is done */
static void my_finale() {}

/* Initialise the memory and set the finale function */
static void initialise() {
    mem_init(memory);
    finale = my_finale;

    // Ask the user for configurable values
    printf("Enter aging time interval:");
    scanf("%d", &AGING_TIME_INTERVAL);

    printf("Enter aging factor: ");
    scanf("%d", &AGING_FACTOR);

    printf("initialised\n");
}

/* The schedule function that is called by the simulator */
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
        increase_age();
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
