using System.ComponentModel;

namespace CalorieTrackerApp;

public class MainForm : Form
{
    private readonly BindingList<Meal> meals = new();

    private TextBox txtNorm = new();
    private ComboBox cmbMealType = new();
    private TextBox txtProduct = new();
    private TextBox txtCalories = new();
    private Button btnAdd = new();
    private Button btnRemove = new();
    private Button btnClear = new();
    private DataGridView grid = new();
    private Label lblTotal = new();
    private ProgressBar progressBar = new();
    private Label lblStatus = new();

    public MainForm()
    {
        Text = "Підрахунок калорій";
        Width = 620;
        Height = 580;
        StartPosition = FormStartPosition.CenterScreen;

        var lblNorm = new Label { Text = "Денна норма (ккал):", Location = new Point(20, 20), AutoSize = true };
        txtNorm.Location = new Point(200, 17);
        txtNorm.Width = 120;
        txtNorm.Text = "2000";
        txtNorm.TextChanged += (_, _) => UpdateSummary();

        var lblMealType = new Label { Text = "Прийом їжі:", Location = new Point(20, 60), AutoSize = true };
        cmbMealType.Location = new Point(200, 57);
        cmbMealType.Width = 200;
        cmbMealType.DropDownStyle = ComboBoxStyle.DropDownList;
        cmbMealType.Items.AddRange(new object[] { "Сніданок", "Обід", "Вечеря", "Перекус" });
        cmbMealType.SelectedIndex = 0;

        var lblProduct = new Label { Text = "Продукт:", Location = new Point(20, 95), AutoSize = true };
        txtProduct.Location = new Point(200, 92);
        txtProduct.Width = 200;

        var lblCalories = new Label { Text = "Калорійність (ккал):", Location = new Point(20, 130), AutoSize = true };
        txtCalories.Location = new Point(200, 127);
        txtCalories.Width = 200;

        btnAdd.Text = "Додати";
        btnAdd.Location = new Point(430, 57);
        btnAdd.Size = new Size(150, 32);
        btnAdd.Click += BtnAdd_Click;

        btnRemove.Text = "Видалити вибране";
        btnRemove.Location = new Point(430, 94);
        btnRemove.Size = new Size(150, 32);
        btnRemove.Click += BtnRemove_Click;

        btnClear.Text = "Очистити день";
        btnClear.Location = new Point(430, 131);
        btnClear.Size = new Size(150, 32);
        btnClear.Click += BtnClear_Click;

        grid.Location = new Point(20, 180);
        grid.Size = new Size(560, 200);
        grid.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right;
        grid.ReadOnly = true;
        grid.AllowUserToAddRows = false;
        grid.AllowUserToDeleteRows = false;
        grid.MultiSelect = false;
        grid.SelectionMode = DataGridViewSelectionMode.FullRowSelect;
        grid.AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill;
        grid.AutoGenerateColumns = false;
        grid.Columns.Add(new DataGridViewTextBoxColumn { DataPropertyName = "MealType", HeaderText = "Прийом їжі" });
        grid.Columns.Add(new DataGridViewTextBoxColumn { DataPropertyName = "Product", HeaderText = "Продукт" });
        grid.Columns.Add(new DataGridViewTextBoxColumn { DataPropertyName = "Calories", HeaderText = "Ккал" });
        grid.DataSource = meals;

        lblTotal.Location = new Point(20, 400);
        lblTotal.AutoSize = true;
        lblTotal.Font = new Font(Font.FontFamily, 11, FontStyle.Bold);

        progressBar.Location = new Point(20, 435);
        progressBar.Size = new Size(560, 28);
        progressBar.Minimum = 0;
        progressBar.Maximum = 100;
        progressBar.Style = ProgressBarStyle.Continuous;

        lblStatus.Location = new Point(20, 475);
        lblStatus.AutoSize = true;
        lblStatus.Font = new Font(Font.FontFamily, 10, FontStyle.Bold);

        Controls.AddRange(new Control[]
        {
            lblNorm, txtNorm,
            lblMealType, cmbMealType,
            lblProduct, txtProduct,
            lblCalories, txtCalories,
            btnAdd, btnRemove, btnClear,
            grid,
            lblTotal, progressBar, lblStatus
        });

        UpdateSummary();
    }

    private void BtnAdd_Click(object? sender, EventArgs e)
    {
        string product = txtProduct.Text.Trim();

        if (string.IsNullOrWhiteSpace(product))
        {
            MessageBox.Show("Введіть назву продукту", "Помилка", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return;
        }

        if (!int.TryParse(txtCalories.Text.Trim(), out int calories) || calories <= 0)
        {
            MessageBox.Show("Введіть коректну калорійність (ціле число більше 0)", "Помилка", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return;
        }

        meals.Add(new Meal
        {
            MealType = cmbMealType.SelectedItem?.ToString() ?? "",
            Product = product,
            Calories = calories
        });

        txtProduct.Clear();
        txtCalories.Clear();
        txtProduct.Focus();

        UpdateSummary();
    }

    private void BtnRemove_Click(object? sender, EventArgs e)
    {
        if (grid.CurrentRow?.DataBoundItem is Meal selected)
        {
            meals.Remove(selected);
            UpdateSummary();
        }
    }

    private void BtnClear_Click(object? sender, EventArgs e)
    {
        if (meals.Count == 0)
            return;

        var answer = MessageBox.Show("Очистити список прийомів їжі за день?", "Підтвердження",
            MessageBoxButtons.YesNo, MessageBoxIcon.Question);

        if (answer == DialogResult.Yes)
        {
            meals.Clear();
            UpdateSummary();
        }
    }

    private void UpdateSummary()
    {
        int total = meals.Sum(m => m.Calories);

        if (!int.TryParse(txtNorm.Text.Trim(), out int norm) || norm <= 0)
        {
            lblTotal.Text = $"Спожито за день: {total} ккал";
            progressBar.Value = 0;
            lblStatus.Text = "Введіть денну норму калорій";
            lblStatus.ForeColor = Color.Gray;
            return;
        }

        double percent = total * 100.0 / norm;

        lblTotal.Text = $"Спожито: {total} з {norm} ккал ({percent:F0}%)";
        progressBar.Value = (int)Math.Min(100, Math.Round(percent));

        if (total > norm)
        {
            lblStatus.Text = $"Норму перевищено на {total - norm} ккал";
            lblStatus.ForeColor = Color.DarkRed;
        }
        else if (percent >= 90)
        {
            lblStatus.Text = $"Майже норма, залишилось {norm - total} ккал";
            lblStatus.ForeColor = Color.DarkOrange;
        }
        else
        {
            lblStatus.Text = $"Можна спожити ще {norm - total} ккал";
            lblStatus.ForeColor = Color.DarkGreen;
        }
    }
}
