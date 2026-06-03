from screens.base_screen import BaseScreen


class CalendarScreen(BaseScreen):
    MONTH_NAMES = ["", "一月", "二月", "三月", "四月", "五月", "六月",
                   "七月", "八月", "九月", "十月", "十一月", "十二月"]

    def draw(self, time_data=None, todo_items=None, **kwargs):
        self.display.fill(self.bg)
        if time_data is None:
            return
        year = time_data["year"]
        month = time_data["month"]
        today = time_data["day"]

        title = f"{year} {self.MONTH_NAMES[month]}"
        cx = self.width // 2
        self.display.text(title, cx - len(title) * 4, 5, self.primary)

        dow_labels = "一 二 三 四 五 六 日"
        self.display.text(dow_labels, 8, 20, self.dim)

        first_weekday = self._first_weekday(year, month)
        days_in_month = self._days_in_month(year, month)

        cell_x = 8
        cell_w = (self.width - 16) // 7
        cell_y = 34
        cell_h = 14

        col = first_weekday
        row = 0
        for day in range(1, days_in_month + 1):
            x = cell_x + col * cell_w
            y = cell_y + row * cell_h
            is_today = day == today
            color = self.accent if is_today else self.fg
            if is_today:
                self.display.fill_rect(x, y, cell_w, cell_h, self.accent)
                color = self.bg
            self.display.text(f"{day:2d}", x + 2, y + 2, color)
            col += 1
            if col > 6:
                col = 0
                row += 1

        list_y = cell_y + (row + 1) * cell_h + 8
        self.display.hline(8, list_y - 4, self.width - 16, self.primary)
        self.display.text("待辦事項", 8, list_y, self.primary)

        items = todo_items or []
        display_items = items[:5]
        for i, item in enumerate(display_items):
            item_y = list_y + 14 + i * 14
            if item_y > self.height - 14:
                break
            icon = " ✓ " if item.get("done") else " ○ "
            self.display.text(
                f"{icon}{item['text'][:16]}",
                8,
                item_y,
                self.fg if not item.get("done") else self.dim,
            )

        if len(items) > 5:
            self.display.text(
                f"...還有 {len(items) - 5} 項",
                8,
                self.height - 12,
                self.dim,
            )

    def _first_weekday(self, year, month):
        if month <= 2:
            month += 12
            year -= 1
        k = year % 100
        j = year // 100
        h = (1 + 13 * (month + 1) // 5 + k + k // 4 + j // 4 - 2 * j) % 7
        return (h + 5) % 7

    def _days_in_month(self, year, month):
        if month == 2:
            if (year % 400 == 0) or (year % 4 == 0 and year % 100 != 0):
                return 29
            return 28
        return [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1]
