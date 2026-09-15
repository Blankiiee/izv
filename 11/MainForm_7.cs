namespace TransportCO2Calculator
{
    public class MainForm : Form
    {
        private const decimal PlaneFactor = 0.255m;
        private const decimal TrainFactor = 0.041m;
        private const decimal CarFactor = 0.192m;
        private const decimal OffsetPricePerKg = 0.5m;

        private ComboBox cmbTransport = null!;
        private NumericUpDown numDistance = null!;
        private Button btnCalculate = null!;
        private Label lblResult = null!;

        public MainForm()
        {
            BuildUi();
        }

        private void BuildUi()
        {
            Text = "Калькулятор викидів CO2 транспорту";
            ClientSize = new Size(420, 280);
            FormBorderStyle = FormBorderStyle.FixedSingle;
            MaximizeBox = false;
            StartPosition = FormStartPosition.CenterScreen;

            var lblTransport = new Label
            {
                Text = "Вид транспорту:",
                Location = new Point(12, 20),
                Size = new Size(150, 20)
            };

            cmbTransport = new ComboBox
            {
                Location = new Point(12, 45),
                Size = new Size(200, 23),
                DropDownStyle = ComboBoxStyle.DropDownList
            };
            cmbTransport.Items.Add("Літак");
            cmbTransport.Items.Add("Потяг");
            cmbTransport.Items.Add("Авто");
            cmbTransport.SelectedIndex = 0;

            var lblDistance = new Label
            {
                Text = "Відстань, км:",
                Location = new Point(12, 85),
                Size = new Size(150, 20)
            };

            numDistance = new NumericUpDown
            {
                Location = new Point(12, 110),
                Size = new Size(150, 23),
                Minimum = 0,
                Maximum = 100000,
                Value = 500
            };

            btnCalculate = new Button
            {
                Text = "Розрахувати",
                Location = new Point(12, 150),
                Size = new Size(150, 35)
            };
            btnCalculate.Click += BtnCalculate_Click;

            lblResult = new Label
            {
                Text = "Викиди CO2: —",
                Location = new Point(12, 200),
                Size = new Size(396, 70),
                Font = new Font("Segoe UI", 10.5F, FontStyle.Bold)
            };

            Controls.Add(lblTransport);
            Controls.Add(cmbTransport);
            Controls.Add(lblDistance);
            Controls.Add(numDistance);
            Controls.Add(btnCalculate);
            Controls.Add(lblResult);
        }

        private void BtnCalculate_Click(object? sender, EventArgs e)
        {
            decimal distance = numDistance.Value;
            decimal factor;
            string transportName = cmbTransport.SelectedItem?.ToString() ?? "";

            if (transportName == "Літак")
            {
                factor = PlaneFactor;
            }
            else if (transportName == "Потяг")
            {
                factor = TrainFactor;
            }
            else
            {
                factor = CarFactor;
            }

            decimal co2Kg = distance * factor;
            decimal offsetCost = co2Kg * OffsetPricePerKg;

            lblResult.Text =
                $"Транспорт: {transportName}\n" +
                $"Відстань: {distance:F0} км\n" +
                $"Викиди CO2: {co2Kg:F2} кг\n" +
                $"Вартість компенсації: {offsetCost:F2} грн";
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
