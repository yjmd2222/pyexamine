class SimilarityScorer:
    def score_user(self, a, b, c, d, e):
        total = 0
        if a > b:
            total += 1
        if b > c:
            total += 1
        if c > d:
            total += 1
        if d > e:
            total += 1
        return total

    def score_item(self, a, b, c, d, e):
        total = 0
        if a < b:
            total += 1
        if b < c:
            total += 1
        if c < d:
            total += 1
        if d < e:
            total += 1
        return total

    def score_pair(self, a, b, c, d, e):
        total = 0
        if a == b:
            total += 2
        if b == c:
            total += 2
        if c == d:
            total += 2
        if d == e:
            total += 2
        return total

    def score_context(self, a, b, c, d, e):
        total = 0
        if a >= b:
            total += 1
        if b >= c:
            total += 1
        if c >= d:
            total += 1
        if d >= e:
            total += 1
        return total

    def score_window(self, a, b, c, d, e):
        total = 0
        if a + b > c:
            total += 1
        if b + c > d:
            total += 1
        if c + d > e:
            total += 1
        if d + e > a:
            total += 1
        return total

    def score_final(self, a, b, c, d, e):
        total = 0
        if a - b > 0:
            total += 1
        if b - c > 0:
            total += 1
        if c - d > 0:
            total += 1
        if d - e > 0:
            total += 1
        return total
