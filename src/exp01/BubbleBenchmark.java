package exp01;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Random;
import java.util.stream.IntStream;

public class BubbleBenchmark{
    /* Every algorithm sorts exactly the same sequence of arrays. */
    static final long SEED = 50;

    // Algorithms
    static final String PASS_PER_ITEM = "PASS_PER_ITEM";
    static final String UNTIL_NO_CHANGE = "UNTIL_NO_CHANGE";
    static final String WHILE_NEEDED = "WHILE_NEEDED";


    // Initial orders of the data
    static final String SORTED = "SORTED";
    static final String REVERSED = "REVERSED";
    static final String RANDOM = "RANDOM";
    static final String NEARLY_SORTED = "NEARLY_SORTED";

    static final List<String> ALGORITHMS = List.of(PASS_PER_ITEM, UNTIL_NO_CHANGE, WHILE_NEEDED);
    static final List<String> ORDERS = List.of(SORTED, REVERSED, RANDOM, NEARLY_SORTED);
    static final int[] SIZES = {10, 100, 1000, 10000};
    
    static final long WARMUP = 1_000_000_000; // 1s per configuration
    static final long MIN_BATCH = 10_000_000; // 10ms
    static final int REPETITIONS = 30; // Measured batches per configuration
    
    record Config(String algorithm, int size, String order) { }

    public static void main(final String[] args) {
        final int run = Integer.parseInt(args[0]);

        final List<Config> configs = new ArrayList<>();
        for (final String algorithm : ALGORITHMS) {
            for (final int size : SIZES) {
                for (final String order : ORDERS) {
                    configs.add(new Config(algorithm, size, order));
                }
            }
        }
        Collections.shuffle(configs, new Random(run)); // Randomized execution order: different in every run

        System.out.println("run,algorithm,size,order,repetition,batch_size,batch_ns");
        for (final Config config : configs) {
            System.err.println("run " + run + ": " + config);
            final Sorter<Integer> sorter = newSorter(config.algorithm());

            // Warm-up
            final Integer[] warmupInput = generate(config.order(), config.size(), new Random(SEED));
            final long warmupEnd = System.nanoTime() + WARMUP;
            while (System.nanoTime() < warmupEnd) {
                timeBatch(sorter, warmupInput, 1);
            }

            // Double the batch size until one batch lasts at least MIN_BATCH
            int batch = 1;
            while (timeBatch(sorter, warmupInput, batch) < MIN_BATCH) {
                batch *= 2;
            }

            // Measurement: same seeded sequence of input arrays for every algorithm
            final Random random = new Random(SEED);
            for (int rep = 0; rep < REPETITIONS; rep++) {
                final Integer[] input = generate(config.order(), config.size(), random);
                final long elapsed = timeBatch(sorter, input, batch);
                System.out.println(run + "," + config.algorithm() + "," + config.size() + "," + config.order()
                        + "," + rep + "," + batch + "," + elapsed);
            }
        }
    }

    /**
     * Sorts copies of the input and returns the elapsed time in ns.
     * The copies are made before the timer starts (the sorters work in place),
     * and the result is checked after the timer stops.
     */
    static long timeBatch(final Sorter<Integer> sorter, final Integer[] input, final int batch) {
        final Integer[][] copies = new Integer[batch][];
        for (int i = 0; i < batch; i++) {
            copies[i] = input.clone();
        }

        final long start = System.nanoTime();
        for (final Integer[] items : copies) {
            sorter.sort(items);
        }
        final long elapsed = System.nanoTime() - start;

        for (int i = 0; i < input.length; i++) {
            if (copies[0][i] != i) {
                throw new AssertionError("Array not sorted correctly by " + sorter.getClass().getSimpleName());
            }
        }
        return elapsed;
    }

    static Sorter<Integer> newSorter(final String algorithm) {
        return switch (algorithm) {
            case PASS_PER_ITEM -> new BubbleSortPassPerItem<>();
            case UNTIL_NO_CHANGE -> new BubbleSortUntilNoChange<>();
            case WHILE_NEEDED -> new BubbleSortWhileNeeded<>();
            default -> throw new IllegalArgumentException(algorithm);
        };
    }

    static Integer[] generate(final String order, final int size, final Random random) {
        final List<Integer> list = new ArrayList<>(IntStream.range(0, size).boxed().toList());
        switch (order) {
            case SORTED -> { }
            case REVERSED -> Collections.reverse(list);
            case RANDOM -> Collections.shuffle(list, random);
            case NEARLY_SORTED -> {
                for (int i = 0; i < (size + 99) / 100; i++) {
                    Collections.swap(list, random.nextInt(size), random.nextInt(size));
                }
            }
            default -> throw new IllegalArgumentException(order);
        }
        return list.toArray(new Integer[0]);
    }
}