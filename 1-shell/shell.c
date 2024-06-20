/* Name: Daan Rosendal
 * Student number: 15229394
 * Study: Bachelor HBO-ICT (Software Engineering) at Windesheim in Zwolle. I follow Operating
 * Systems as a "bijvak".
 *
 * This file contains the implementation of the shell. The shell is an interactive command-line
 * interpreter that can execute commands. The shell supports the following functionalities:
 * - External commands
 * - Built-in commands: exit, cd
 * - Sequences
 * - Pipes
 * - Redirects
 * - Detached commands
 * - Subshells
 * - Environment variables (using set and unset)
 */

#define _POSIX_C_SOURCE 200112L

#include "shell.h"
#include "arena.h"
#include "front.h"
#include "parser/ast.h"
#include <fcntl.h>
#include <pwd.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>

/* Signal handler for SIGINT.
 *
 * This function is called when the SIGINT signal is received (e.g., when Ctrl+C is pressed). It
 * sets up the signal handler to call itself again, ensuring that SIGINT is consistently handled.
 */
void sigint_handler() { signal(SIGINT, sigint_handler); }

/* Initialize the shell.
 *
 * This function sets up the signal handler for SIGINT, ensuring that the shell consistently handles
 * the interrupt signal.
 */
void initialize(void) { signal(SIGINT, sigint_handler); }

/* Clean up the shell.
 *
 * This function is called when the shell is about to exit. It performs any necessary cleanup.
 */
void shell_exit(void) {}

/* Execute a sequence of commands.
 *
 * This function runs the first command in the sequence, followed by the second command.
 *
 * node: the AST node representing the sequence of commands
 */
void execute_sequence_command(node_t *node) {
    run_command(node->sequence.first);
    run_command(node->sequence.second);
}

/* Execute a subshell command.
 *
 * This function creates a child process to execute the command within a subshell.
 *
 * node: the AST node representing the subshell command
 */
void execute_subshell_command(node_t *node) {
    pid_t pid = fork();
    if (pid < 0) {
        perror("fork");
        exit(EXIT_FAILURE);
    } else if (pid == 0) { // Child process
        run_command(node->subshell.child);
        exit(EXIT_SUCCESS);
    } else { // Parent process
        int status;
        waitpid(pid, &status, 0);
    }
}

// These constants are used to index the read and write ends of a pipe.
const int PIPE_INPUT = 0;
const int PIPE_OUTPUT = 1;

/* Fork processes for each command in a pipeline.
 *
 * This function creates a child process for each command in a pipeline, setting up the necessary
 * pipes for communication between the processes.
 *
 * node: the AST node representing the pipeline command
 * pipe_fds: an array of pipe file descriptors
 * pipe_count: the number of pipes in the pipeline
 * pipeline_commands: an array of AST nodes representing the commands in the pipeline
 */
void fork_processes(node_t *node, int pipe_fds[][2], size_t pipe_count,
                    node_t **pipeline_commands) {
    for (size_t i = 0; i < node->pipe.n_parts; i++) {
        pid_t pid = fork();
        if (pid == -1) {
            perror("fork");
            exit(EXIT_FAILURE);
        } else if (pid == 0) { // Child process
            // Close unused write ends of previous pipes
            for (size_t j = 0; j < i; j++) {
                close(pipe_fds[j][PIPE_OUTPUT]);
            }
            // Close unused read ends of subsequent pipes
            for (size_t j = i + 1; j < pipe_count; j++) {
                close(pipe_fds[j][PIPE_INPUT]);
                close(pipe_fds[j][PIPE_OUTPUT]);
            }

            // Redirect input/output
            if (i != 0) {
                dup2(pipe_fds[i - 1][PIPE_INPUT], STDIN_FILENO);
                close(pipe_fds[i - 1][PIPE_INPUT]);
            }
            if (i != pipe_count) {
                dup2(pipe_fds[i][PIPE_OUTPUT], STDOUT_FILENO);
                close(pipe_fds[i][PIPE_OUTPUT]);
            }

            run_command(pipeline_commands[i]);
            exit(EXIT_SUCCESS);
        }
    }
}

/* Execute a pipeline command.
 *
 * This function creates a pipeline of commands, with the output of each command connected to the
 * input of the next command.
 *
 * node: the AST node representing the pipeline command
 */
void execute_pipe_command(node_t *node) {
    size_t pipe_count = node->pipe.n_parts - 1;

    int pipe_fds[pipe_count][2];

    // Create pipes
    for (size_t i = 0; i < pipe_count; i++) {
        if (pipe(pipe_fds[i]) == -1) {
            perror("pipe");
            exit(EXIT_FAILURE);
        }
    }

    // Fork processes for each command in the pipeline
    fork_processes(node, pipe_fds, pipe_count, node->pipe.parts);

    // Close all pipe ends in the parent process
    for (size_t i = 0; i < pipe_count; i++) {
        close(pipe_fds[i][PIPE_INPUT]);
        close(pipe_fds[i][PIPE_OUTPUT]);
    }

    // Wait for all child processes to finish
    for (size_t i = 0; i < node->pipe.n_parts; i++) {
        int status;
        wait(&status);
    }
}

/* Execute a detached command.
 *
 * This function creates a child process to execute the command in the background, without waiting
 * for its completion.
 *
 * node: the AST node representing the detached command
 */
void execute_detach_command(node_t *node) {
    pid_t pid = fork();
    if (pid == -1) {
        perror("fork");
        exit(EXIT_FAILURE);
    } else if (pid == 0) { // Child process
        run_command(node->detach.child);
        exit(EXIT_SUCCESS);
    }
    // Parent process continues without waiting for the child
}

/* Open a file for redirection.
 *
 * This function opens a file for redirection based on the specified mode.
 *
 * node: the AST node representing the redirect command
 *
 * Returns:
 * the file descriptor of the opened file
 */
int open_file_for_redirect(node_t *node) {
    int fd;

    if (node->redirect.mode == REDIRECT_APPEND) {
        fd = open(node->redirect.target, O_WRONLY | O_CREAT | O_APPEND, 0644);
    } else if (node->redirect.mode == REDIRECT_OUTPUT) {
        fd = open(node->redirect.target, O_WRONLY | O_CREAT | O_TRUNC, 0644);
    } else if (node->redirect.mode == REDIRECT_INPUT) {
        fd = open(node->redirect.target, O_RDONLY);
    } else if (node->redirect.mode == REDIRECT_DUP) {
        fd = node->redirect.fd2;
    } else {
        perror("Invalid redirect mode");
        exit(EXIT_FAILURE);
    }

    return fd;
}

/* Execute a redirect command.
 *
 * This function creates a child process to execute the command with input/output redirected as
 * specified.
 *
 * node: the AST node representing the redirect command
 */
void execute_redirect_command(node_t *node) {
    pid_t pid = fork();

    if (pid == -1) {
        perror("fork");
        exit(EXIT_FAILURE);
    } else if (pid == 0) { // Child process
        int fd = open_file_for_redirect(node);

        if (fd == -1) {
            perror("open");
            exit(EXIT_FAILURE);
        }

        if (dup2(fd, node->redirect.fd) == -1) {
            perror("dup2");
            close(fd);
            exit(EXIT_FAILURE);
        }

        if (node->redirect.fd != fd) {
            close(fd);
        }

        run_command(node->redirect.child);
        exit(EXIT_FAILURE);
    } else { // Parent process
        int status;
        waitpid(pid, &status, 0);
    }
}

/* Execute an exit command.
 *
 * This function exits the shell with the specified exit code.
 *
 * node: the AST node representing the exit command
 */
void execute_exit_command(node_t *node) {
    if (node->command.argc == 1) {
        exit(42);
    } else {
        exit(atoi(node->command.argv[1]));
    }
}

/* Execute a cd command.
 *
 * This function changes the current working directory as specified by the command arguments.
 *
 * node: the AST node representing the cd command
 */
void execute_cd_command(node_t *node) {
    if (node->command.argc == 1) {
        const char *home = getenv("HOME");
        if (home != NULL) {
            chdir(home);
        }
    } else {
        chdir(node->command.argv[1]);
    }
}

/* Execute a set command.
 *
 * This function sets an environment variable with the specified name and value.
 *
 * node: the AST node representing the set command
 */
void execute_set_command(node_t *node) {
    if (node->command.argc != 2) {
        perror("Usage: set <env_var=value>");
        exit(EXIT_FAILURE);
    } else {
        char *env_var = strtok(node->command.argv[1], "=");
        char *value = strtok(NULL, "=");
        if (env_var == NULL || value == NULL) {
            perror("Invalid format. Usage: set <env_var=value>");
            exit(EXIT_FAILURE);
        }
        if (setenv(env_var, value, 1) != 0) {
            perror("setenv");
            exit(EXIT_FAILURE);
        }
    }
}

/* Execute an unset command.
 *
 * This function unsets (removes) the specified environment variable.
 *
 * node: the AST node representing the unset command
 */
void execute_unset_command(node_t *node) {
    if (node->command.argc < 2) {
        perror("Usage: unset <variable>");
        exit(EXIT_FAILURE);
    } else {
        if (unsetenv(node->command.argv[1]) != 0) {
            perror("unsetenv");
            exit(EXIT_FAILURE);
        }
    }
}

/* Execute an external command.
 *
 * This function executes an external command using execvp in a child process.
 *
 * node: the AST node representing the external command
 */
void execute_external_command(node_t *node) {
    pid_t pid = fork();
    if (pid < 0) {
        perror("fork");
        exit(EXIT_FAILURE);
    } else if (pid == 0) { // Child process
        execvp(node->command.program, node->command.argv);
        perror("execvp");
        exit(EXIT_FAILURE);
    } else { // Parent process
        int status;
        signal(SIGINT, SIG_IGN);
        waitpid(pid, &status, 0);
    }
}

/* Execute a simple command.
 *
 * This function determines the type of simple command (e.g., exit, cd, set, unset, external) and
 * executes it accordingly.
 *
 * node: the AST node representing the simple command
 */
void execute_simple_command(node_t *node) {
    if (strcmp(node->command.program, "exit") == 0) {
        execute_exit_command(node);
    } else if (strcmp(node->command.program, "cd") == 0) {
        execute_cd_command(node);
    } else if (strcmp(node->command.program, "set") == 0) {
        execute_set_command(node);
    } else if (strcmp(node->command.program, "unset") == 0) {
        execute_unset_command(node);
    } else {
        execute_external_command(node);
    }
}

/* Run a command.
 *
 * This function dispatches the execution of different types of commands based on the type of the
 * AST node.
 *
 * node: the AST node representing the command to execute
 */
void run_command(node_t *node) {
    arena_push();

    switch (node->type) {
    case NODE_SEQUENCE:
        execute_sequence_command(node);
        break;
    case NODE_SUBSHELL:
        execute_subshell_command(node);
        break;
    case NODE_PIPE:
        execute_pipe_command(node);
        break;
    case NODE_DETACH:
        execute_detach_command(node);
        break;
    case NODE_REDIRECT:
        execute_redirect_command(node);
        break;
    case NODE_COMMAND:
        execute_simple_command(node);
        break;
    default:
        perror("Invalid command type");
        exit(EXIT_FAILURE);
    }

    arena_pop();
}
