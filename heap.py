class MaxHeap(object):

    def __init__(self, data):
        self._data = data

        self._heap_size = len(self._data)

        self._build_max_heap()

    def __len__(self):
        return self._heap_size

    def _left(self, i):
        return 2 * i + 1

    def _right(self, i):
        return 2 * i + 2

    def _swap(self, a, b):
        self._data[a], self._data[b] = self._data[b], self._data[a]

    def _max_heapify(self, i):

        left = self._left(i)
        right = self._right(i)

        if left < self._heap_size and self._data[left][0] > self._data[i][0]:
            largest = left
        else:
            largest = i

        if right < self._heap_size and self._data[right][0] > self._data[largest][0]:
            largest = right

        if largest != i:
            self._swap(i, largest)
            self._max_heapify(largest)

    def _build_max_heap(self):
        self._size = len(self._data)

        start = (self._size - 1) // 2
        for i in range(start, -1, -1):
            self._max_heapify(i)

    def sort(self):
        for i in range(self._size - 1, 0, -1):
            self._swap(0, i)

            self._heap_size -= 1

            self._max_heapify(0)

    def get_items(self):
        return self._data

    def pop(self):
        if self._heap_size < 1:
            raise IndexError("Heap is empty")

        max_element = self._data[0]
        self._swap(0, self._heap_size - 1)
        self._heap_size -= 1
        self._max_heapify(0)

        self._data.pop()

        return max_element