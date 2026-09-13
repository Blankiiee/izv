namespace SleepCalculator
{
    // Норми тривалості сну за віковими категоріями (спрощено, у годинах)
    internal class AgeCategory
    {
        public string Name = "";
        public double MinHours;
        public double MaxHours;
    }

    public class MainForm : Form
    {
        private readonly List<AgeCategory> _categories = new()
        {
            new AgeCategory { Name = "Немовля (0-1 рік)", MinHours = 12, MaxHours = 16 },
            new AgeCategory { Name = "Дитина (1-13 років)", MinHours = 9, MaxHours = 12 },
            new AgeCategory { Name = "Підліток (14-17 років)", MinHours = 8, MaxHours = 10 },
            new AgeCategory { Name = "Дорослий (18-64 роки)", MinHours = 7, MaxHours = 9 },
            new AgeCategory { Name = "Похилий вік (65+ років)", MinHours = 7, MaxHours = 8 }
        };

        private DateTimePicker dtpSleepTime = null!;
        private DateTimePicker dtpWakeTime = null!;
        private ComboBox cmbAgeCategory = null!;
        private Button btnCalculate = null!;
        private Label lblResult = null!;

        public MainForm()
        {
            BuildUi();
        }

        private void BuildUi()
        {
            Text = "Калькулятор тривалості сну";
            ClientSize = new Size(420, 320);
            FormBorderStyle = FormBorderStyle.FixedSingle;
            MaximizeBox = false;
            StartPosition = FormStartPosition.CenterScreen;

            var lblSleep = new Label
            {
                Text = "Час, коли лягли спати:",
                Location = new Point(12, 20),
                Size = new Size(200, 20)
            };

            dtpSleepTime = new DateTimePicker
            {
                Location = new Point(12, 45),
                Size = new Size(150, 23),
                Format = DateTimePickerFormat.Time,
                ShowUpDown = true,
                Value = DateTime.Today.AddHours(23)
            };

            var lblWake = new Label
            {
                Text = "Час пробудження:",
                Location = new Point(12, 80),
                Size = new Size(200, 20)
            };

            dtpWakeTime = new DateTimePicker
            {
                Location = new Point(12, 105),
                Size = new Size(150, 23),
                Format = DateTimePickerFormat.Time,
                ShowUpDown = true,
                Value = DateTime.Today.AddHours(7)
            };

            var lblAge = new Label
            {
                Text = "Вікова категорія:",
                Location = new Point(12, 140),
                Size = new Size(200, 20)
            };

            cmbAgeCategory = new ComboBox
            {
                Location = new Point(12, 165),
                Size = new Size(280, 23),
                DropDownStyle = ComboBoxStyle.DropDownList
            };
            foreach (var category in _categories)
            {
                cmbAgeCategory.Items.Add(category.Name);
            }
            cmbAgeCategory.SelectedIndex = 3; // За замовчуванням "Дорослий"

            btnCalculate = new Button
            {
                Text = "Розрахувати",
                Location = new Point(12, 205),
                Size = new Size(150, 35)
            };
            btnCalculate.Click += BtnCalculate_Click;

            lblResult = new Label
            {
                Text = "Тривалість сну: —",
                Location = new Point(12, 255),
                Size = new Size(396, 55),
                Font = new Font("Segoe UI", 11F, FontStyle.Bold)
            };

            Controls.Add(lblSleep);
            Controls.Add(dtpSleepTime);
            Controls.Add(lblWake);
            Controls.Add(dtpWakeTime);
            Controls.Add(lblAge);
            Controls.Add(cmbAgeCategory);
            Controls.Add(btnCalculate);
            Controls.Add(lblResult);
        }

        private void BtnCalculate_Click(object? sender, EventArgs e)
        {
            TimeSpan sleepTime = dtpSleepTime.Value.TimeOfDay;
            TimeSpan wakeTime = dtpWakeTime.Value.TimeOfDay;

            TimeSpan duration = wakeTime - sleepTime;

            // Якщо прокинулись "раніше" за годинником — значить, пробудження було наступного дня
            if (duration <= TimeSpan.Zero)
            {
                duration += TimeSpan.FromHours(24);
            }

            double hours = duration.TotalHours;

            AgeCategory category = _categories[cmbAgeCategory.SelectedIndex];

            string verdict;
            if (hours < category.MinHours)
            {
                verdict = "Недосип";
            }
            else if (hours > category.MaxHours)
            {
                verdict = "Пересип";
            }
            else
            {
                verdict = "Норма";
            }

            lblResult.Text =
                $"Тривалість сну: {(int)duration.TotalHours} год {duration.Minutes} хв{Environment.NewLine}" +
                $"Норма для «{category.Name}»: {category.MinHours}-{category.MaxHours} год{Environment.NewLine}" +
                $"Висновок: {verdict}";
        }
    }

    internal static class Program
    {
        [STAThread]
        static void Main()
        {
            ApplicationConfiguration.Initialize();
            Application.Run(new MainForm());
        }
    }
}
