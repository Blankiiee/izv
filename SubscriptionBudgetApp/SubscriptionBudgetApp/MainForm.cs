using System.ComponentModel;
using System.Globalization;

namespace SubscriptionBudgetApp;

public class MainForm : Form
{
    private readonly BindingList<Subscription> subscriptions = new();

    private TextBox txtSalary = new();
    private ComboBox cmbName = new();
    private TextBox txtPrice = new();
    private Button btnAdd = new();
    private Button btnRemove = new();
    private DataGridView grid = new();
    private Label lblTotal = new();
    private Label lblRemaining = new();
    private Label lblShare = new();

    public MainForm()
    {
        Text = "Бюджет підписок";
        Width = 620;
        Height = 560;
        StartPosition = FormStartPosition.CenterScreen;

        var lblSalary = new Label { Text = "Місячна зарплата (грн):", Location = new Point(20, 20), AutoSize = true };
        txtSalary.Location = new Point(210, 17);
        txtSalary.Width = 150;
        txtSalary.TextChanged += (_, _) => UpdateSummary();

        var lblName = new Label { Text = "Назва підписки:", Location = new Point(20, 60), AutoSize = true };
        cmbName.Location = new Point(210, 57);
        cmbName.Width = 200;
        cmbName.DropDownStyle = ComboBoxStyle.DropDown; // можна обрати зі списку або ввести свою
        cmbName.Items.AddRange(new object[]
        {
            "Netflix", "Spotify", "YouTube Premium", "Apple Music",
            "Disney+", "ChatGPT Plus", "Microsoft 365", "Xbox Game Pass"
        });

        var lblPrice = new Label { Text = "Ціна на місяць (грн):", Location = new Point(20, 95), AutoSize = true };
        txtPrice.Location = new Point(210, 92);
        txtPrice.Width = 200;

        btnAdd.Text = "Додати";
        btnAdd.Location = new Point(430, 55);
        btnAdd.Size = new Size(150, 32);
        btnAdd.Click += BtnAdd_Click;

        btnRemove.Text = "Видалити вибране";
        btnRemove.Location = new Point(430, 92);
        btnRemove.Size = new Size(150, 32);
        btnRemove.Click += BtnRemove_Click;

        grid.Location = new Point(20, 140);
        grid.Size = new Size(560, 230);
        grid.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right;
        grid.ReadOnly = true;
        grid.AllowUserToAddRows = false;
        grid.AllowUserToDeleteRows = false;
        grid.MultiSelect = false;
        grid.SelectionMode = DataGridViewSelectionMode.FullRowSelect;
        grid.AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill;
        grid.AutoGenerateColumns = false;
        grid.Columns.Add(new DataGridViewTextBoxColumn { DataPropertyName = "Name", HeaderText = "Підписка" });
        grid.Columns.Add(new DataGridViewTextBoxColumn
        {
            DataPropertyName = "Price",
            HeaderText = "Ціна (грн/міс)",
            DefaultCellStyle = new DataGridViewCellStyle { Format = "N2" }
        });
        grid.DataSource = subscriptions;

        lblTotal.Location = new Point(20, 390);
        lblTotal.AutoSize = true;
        lblTotal.Font = new Font(Font.FontFamily, 11, FontStyle.Bold);

        lblRemaining.Location = new Point(20, 420);
        lblRemaining.AutoSize = true;
        lblRemaining.Font = new Font(Font.FontFamily, 11, FontStyle.Bold);

        lblShare.Location = new Point(20, 452);
        lblShare.AutoSize = true;

        Controls.AddRange(new Control[]
        {
            lblSalary, txtSalary,
            lblName, cmbName,
            lblPrice, txtPrice,
            btnAdd, btnRemove,
            grid,
            lblTotal, lblRemaining, lblShare
        });

        UpdateSummary();
    }

    // Приймає і крапку, і кому як роздільник
    private static bool TryParseDecimal(string text, out decimal value)
    {
        text = text.Trim().Replace(',', '.');
        return decimal.TryParse(text, NumberStyles.Number, CultureInfo.InvariantCulture, out value);
    }

    private void BtnAdd_Click(object? sender, EventArgs e)
    {
        string name = cmbName.Text.Trim();

        if (string.IsNullOrWhiteSpace(name))
        {
            MessageBox.Show("Введіть назву підписки", "Помилка", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return;
        }

        if (!TryParseDecimal(txtPrice.Text, out decimal price) || price <= 0)
        {
            MessageBox.Show("Введіть коректну ціну підписки", "Помилка", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return;
        }

        subscriptions.Add(new Subscription { Name = name, Price = price });

        cmbName.Text = "";
        txtPrice.Clear();
        cmbName.Focus();

        UpdateSummary();
    }

    private void BtnRemove_Click(object? sender, EventArgs e)
    {
        if (grid.CurrentRow?.DataBoundItem is Subscription selected)
        {
            subscriptions.Remove(selected);
            UpdateSummary();
        }
    }

    private void UpdateSummary()
    {
        decimal total = subscriptions.Sum(s => s.Price);
        lblTotal.Text = $"Загальні витрати на підписки: {total:N2} грн/міс";

        if (!TryParseDecimal(txtSalary.Text, out decimal salary) || salary <= 0)
        {
            lblRemaining.Text = "Введіть зарплату, щоб побачити залишок";
            lblRemaining.ForeColor = Color.Gray;
            lblShare.Text = "";
            return;
        }

        decimal remaining = salary - total;
        decimal share = total / salary * 100;

        lblRemaining.Text = remaining >= 0
            ? $"Залишиться від зарплати: {remaining:N2} грн"
            : $"Не вистачає: {Math.Abs(remaining):N2} грн";
        lblRemaining.ForeColor = remaining >= 0 ? Color.DarkGreen : Color.DarkRed;

        lblShare.Text = $"Підписки займають {share:F1}% зарплати";
    }
}
