namespace CalorieTracker
{
    public class MainForm : Form
    {
        private TextBox txtProduct = null!;
        private NumericUpDown numCalories = null!;
        private Button btnAdd = null!;
        private ListBox lstMeals = null!;
        private NumericUpDown numDailyNorm = null!;
        private ProgressBar progressBar = null!;
        private Label lblTotal = null!;
        private Label lblStatus = null!;

        private int _totalCalories = 0;

        public MainForm()
        {
            BuildUi();
        }

        private void BuildUi()
        {
            Text = "Лічильник калорій";
            ClientSize = new Size(460, 470);
            FormBorderStyle = FormBorderStyle.FixedSingle;
            MaximizeBox = false;
            StartPosition = FormStartPosition.CenterScreen;

            var lblProduct = new Label
            {
                Text = "Продукт:",
                Location = new Point(12, 15),
                Size = new Size(100, 20)
            };

            txtProduct = new TextBox
            {
                Location = new Point(12, 38),
                Size = new Size(220, 23)
            };

            var lblCalories = new Label
            {
                Text = "Калорійність, ккал:",
                Location = new Point(250, 15),
                Size = new Size(150, 20)
            };

            numCalories = new NumericUpDown
            {
                Location = new Point(250, 38),
                Size = new Size(100, 23),
                Minimum = 0,
                Maximum = 10000,
                Value = 100
            };

            btnAdd = new Button
            {
                Text = "Додати",
                Location = new Point(360, 37),
                Size = new Size(88, 25)
            };
            btnAdd.Click += BtnAdd_Click;

            lstMeals = new ListBox
            {
                Location = new Point(12, 75),
                Size = new Size(436, 180)
            };

            var lblNorm = new Label
            {
                Text = "Денна норма, ккал:",
                Location = new Point(12, 270),
                Size = new Size(150, 20)
            };

            numDailyNorm = new NumericUpDown
            {
                Location = new Point(12, 293),
                Size = new Size(120, 23),
                Minimum = 500,
                Maximum = 10000,
                Value = 2000,
                Increment = 50
            };
            numDailyNorm.ValueChanged += (s, e) => UpdateProgress();

            lblTotal = new Label
            {
                Text = "Сумарно спожито: 0 ккал",
                Location = new Point(12, 335),
                Size = new Size(436, 25),
                Font = new Font("Segoe UI", 10.5F, FontStyle.Bold)
            };

            progressBar = new ProgressBar
            {
                Location = new Point(12, 365),
                Size = new Size(436, 25),
                Minimum = 0,
                Maximum = 100,
                Value = 0
            };

            lblStatus = new Label
            {
                Text = "",
                Location = new Point(12, 400),
                Size = new Size(436, 40),
                Font = new Font("Segoe UI", 10F, FontStyle.Bold)
            };

            Controls.Add(lblProduct);
            Controls.Add(txtProduct);
            Controls.Add(lblCalories);
            Controls.Add(numCalories);
            Controls.Add(btnAdd);
            Controls.Add(lstMeals);
            Controls.Add(lblNorm);
            Controls.Add(numDailyNorm);
            Controls.Add(lblTotal);
            Controls.Add(progressBar);
            Controls.Add(lblStatus);
        }

        private void BtnAdd_Click(object? sender, EventArgs e)
        {
            string product = txtProduct.Text.Trim();
            int calories = (int)numCalories.Value;

            if (string.IsNullOrEmpty(product))
            {
                MessageBox.Show("Вкажіть назву продукту.", "Помилка", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            lstMeals.Items.Add($"{product} — {calories} ккал");
            _totalCalories += calories;

            txtProduct.Clear();
            numCalories.Value = 100;
            txtProduct.Focus();

            UpdateProgress();
        }

        private void UpdateProgress()
        {
            int norm = (int)numDailyNorm.Value;
            lblTotal.Text = $"Сумарно спожито: {_totalCalories} ккал з {norm} ккал";

            int percent = norm > 0 ? (int)((double)_totalCalories / norm * 100) : 0;
            int clampedPercent = Math.Min(Math.Max(percent, 0), 100);
            progressBar.Value = clampedPercent;

            if (_totalCalories < norm)
            {
                lblStatus.Text = $"До норми залишилось {norm - _totalCalories} ккал.";
                lblStatus.ForeColor = Color.DarkGreen;
                progressBar.ForeColor = Color.Green;
            }
            else if (_totalCalories == norm)
            {
                lblStatus.Text = "Денну норму досягнуто точно.";
                lblStatus.ForeColor = Color.DarkOrange;
            }
            else
            {
                lblStatus.Text = $"Перевищення норми на {_totalCalories - norm} ккал.";
                lblStatus.ForeColor = Color.DarkRed;
            }
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
