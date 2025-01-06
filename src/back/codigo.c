#include <stdio.h>

// Function prototypes
void greet();
int add(int a, int b);
void printArray(int arr[], int size);

int main() {
    greet();

    int sum = add(5, 3);
    printf("Sum: %d\n", sum);

    int arr[] = { 1, 2, 3, 4, 5 };
    printArray(arr, 5);

    return 0;
}

// Function to print a greeting message
void greet() {
    printf("Hello, welcome to the program!\n");
}

// Function to add two integers
int add(int a, int b) {
    return a + b;
}

// Function to print the elements of an array
void printArray(int arr[], int size) {
    printf("Array elements: ");
    for (int i = 0; i < size; i++) {
        printf("%d ", arr[i]);
    }
    printf("\n");
}