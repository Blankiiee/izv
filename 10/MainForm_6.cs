namespace ScreenTimeCalculator
{
    public class MainForm : Form
    {
        private NumericUpDown numHours = null!;
        private Button btnCalculate = null!;
        private Label lblWeek = null!;
        private Label lblYear = null!;
        private Label lblWarning = null!;

        public MainForm()
        {
            BuildUi();
        }

        private void BuildUi()
        {
            Text = "Калькулятор екранного часу";
            ClientSize = new Size(420, 280);
            FormBorderStyle = FormBorderStyle.FixedSingle;
            MaximizeBox = false;
            StartPosition = FormStartPosition.CenterScreen;

            var lblHours = new Label
            {
                Text = "Годин за день у телефоні/ПК:",
                Location = new Point(12, 20),
                Size = new Size(250, 20)
            };

            numHours = new NumericUpDown
            {
                Location = new Point(12, 45),
                Size = new Size(100, 23),
                Minimum = 0,
                Maximum = 24,
                DecimalPlaces = 1,
                Increment = 0.5m,
                Value = 4
            };

            btnCalculate = new Button
            {
                Text = "Розрахувати",
                Location = new Point(12, 85),
                Size = new Size(150, 35)
            };
            btnCalculate.Click += BtnCalculate_Click;

            lblWeek = new Label
            {
                Text = "За тиждень: —",
                Location = new Point(12, 140),
                Size = new Size(396, 25),
                Font = new Font("Segoe UI", 10F)
            };

            lblYear = new Label
            {
                Text = "За рік: —",
                Location = new Point(12, 170),
                Size = new Size(396, 25),
                Font = new Font("Segoe UI", 10F)
            };

            lblWarning = new Label
            {
                Text = "",
                Location = new Point(12, 210),
                Size = new Size(396, 55),
                Font = new Font("Segoe UI", 10F, FontStyle.Bold),
                ForeColor = Color.DarkRed
            };

            Controls.Add(lblHours);
            Controls.Add(numHours);
            Controls.Add(btnCalculate);
            Controls.Add(lblWeek);
            Controls.Add(lblYear);
            Controls.Add(lblWarning);
        }

        private void BtnCalculate_Click(object? sender, EventArgs e)
        {
            decimal hoursPerDay = numHours.Value;
            decimal hoursPerWeek = hoursPerDay * 7;
            decimal hoursPerYear = hoursPerDay * 365;
            decimal daysPerYear = hoursPerYear / 24;

            lblWeek.Text = $"За тиждень: {hoursPerWeek:F1} год";
            lblYear.Text = $"За рік: {hoursPerYear:F0} год (~{daysPerYear:F1} діб)";

            if (hoursPerDay >= 8)
            {
                lblWarning.Text = "Увага: дуже високий рівень екранного часу! Це може негативно вплинути на здоров'я, сон та зір.";
            }
            else if (hoursPerDay >= 5)
            {
                lblWarning.Text = "Помірно високий екранний час. Варто робити перерви та стежити за самопочуттям.";
            }
            else
            {
                lblWarning.Text = "Екранний час у прийнятних межах.";
                lblWarning.ForeColor = Color.DarkGreen;
                return;
            }

            lblWarning.ForeColor = Color.DarkRed;
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
