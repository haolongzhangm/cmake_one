#include "api.h"
#include <cstdio>
#include <cstdlib>

void test_asan() {
    int* p = (int*)(malloc(10 * sizeof(int)));
    for (int i = 0; i < 10; i++) {
        p[i] = i;
    }
    printf("test asan %d\n", p[5]);
    free(p);

    printf("test asan %d\n", p[5]);
}

void hello_api() {
    printf("Hello API!\n");
    // test_asan();
}
