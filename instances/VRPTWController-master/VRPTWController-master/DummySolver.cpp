#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <unistd.h>
#define SECONDS 1e6
int main(int argc, char const* argv[]) {
    uint8_t a = 0;
    srand(time(NULL));

    // while(a < 2) {
        printf("Route #1: 70 53 30\nRoute #2: 20  66  65  71  35  34  78  77  28\nRoute #3: 92  98  91  44  14  38  86  16  61  85 100  37\nRoute #4: 2  57  15  43  42  87  97  95  94  13  58\nRoute #5: 73  22  41  23  67  39  56  75  74  72  21  40\nRoute #6: 52  88  62  19  11  64  63  90  32  10  31\nRoute #7: 6  96  59  99  93  5  84  17  45  83  60  89\nRoute #8: 26  12  80  68  29  24  55  4  25  54\nRoute #9: 27  69  76  3  79  9  51  81  33  50  1\nRoute #10: 18  7  82  8  46  36  49  47  48\nCost 932.1\n");

        fflush(stdout);
        a += 1;
        usleep(2 * SECONDS);

        printf("Route #1: 53 70\nRoute #2: 30  20  66  65  71  35  34  78  77  28\nRoute #3: 92  98  91  44  14  38  86  16  61  85 100  37\nRoute #4: 2  57  15  43  42  87  97  95  94  13  58\nRoute #5: 73  22  41  23  67  39  56  75  74  72  21  40\nRoute #6: 52  88  62  19  11  64  63  90  32  10  31\nRoute #7: 6  96  59  99  93  5  84  17  45  83  60  89\nRoute #8: 26  12  80  68  29  24  55  4  25  54\nRoute #9: 27  69  76  3  79  9  51  81  33  50  1\nRoute #10: 18  7  82  8  46  36  49  47  48\nCost 932.1\n");
        fflush(stdout);
        usleep(2 * SECONDS);
        
        printf("Route #1: 53\nRoute #2: 70  30  20  66  65  71  35  34  78  77  28\nRoute #3: 92  98  91  44  14  38  86  16  61  85 100  37\nRoute #4: 2  57  15  43  42  87  97  95  94  13  58\nRoute #5: 73  22  41  23  67  39  56  75  74  72  21  40\nRoute #6: 52  88  62  19  11  64  63  90  32  10  31\nRoute #7: 6  96  59  99  93  5  84  17  45  83  60  89\nRoute #8: 26  12  80  68  29  24  55  4  25  54\nRoute #9: 27  69  76  3  79  9  51  81  33  50  1\nRoute #10: 18  7  82  8  46  36  49  47  48\nCost 932.1\n");
        
        fflush(stdout);
        usleep(2 * SECONDS);

    // }
    return 0;
}
