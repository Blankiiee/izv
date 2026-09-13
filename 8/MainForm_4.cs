using System.Security.Cryptography;
using System.Text;

namespace PasswordGenerator
{
    public class MainForm : Form
    {
        private const string LowerChars = "abcdefghijklmnopqrstuvwxyz";
        private const string UpperChars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
        private const string DigitChars = "0123456789";
        private const string SpecialChars = "!@#$%^&*()_-+=<>?";

        private NumericUpDown numLength = null!;
        private CheckBox chkDigits = null!;
        private CheckBox chkUpper = null!;
        private CheckBox chkSpecial = null!;
        private Button btnGenerate = null!;
        private TextBox txtPassword = null!;
        private Button btnCopy = null!;
        private Label lblStrength = null!;

        public MainForm()
        {
            BuildUi();
        }

        private void BuildUi()
        {
            Text = "Генератор паролів";
            ClientSize = new Size(420, 300);
            FormBorderStyle = FormBorderStyle.FixedSingle;
            MaximizeBox = false;
            StartPosition = FormStartPosition.CenterScreen;

            var lblLength = new Label
            {
                Text = "Довжина пароля:",
                Location = new Point(12, 20),
                Size = new Size(140, 20)
            };

            numLength = new NumericUpDown
            {
                Location = new Point(160, 18),
                Size = new Size(80, 23),
                Minimum = 4,
                Maximum = 64,
                Value = 12
            };

            chkDigits = new CheckBox
            {
                Text = "Цифри (0-9)",
                Location = new Point(12, 55),
                Size = new Size(200, 24),
                Checked = true
            };

            chkUpper = new CheckBox
            {
                Text = "Великі літери (A-Z)",
                Location = new Point(12, 85),
                Size = new Size(200, 24),
                Checked = true
            };

            chkSpecial = new CheckBox
            {
                Text = "Спецсимволи (!@#$%^&* ...)",
                Location = new Point(12, 115),
                Size = new Size(250, 24),
                Checked = false
            };

            btnGenerate = new Button
            {
                Text = "Згенерувати пароль",
                Location = new Point(12, 155),
                Size = new Size(180, 35)
            };
            btnGenerate.Click += BtnGenerate_Click;

            txtPassword = new TextBox
            {
                Location = new Point(12, 205),
                Size = new Size(300, 25),
                ReadOnly = true,
                Font = new Font("Consolas", 11F)
            };

            btnCopy = new Button
            {
                Text = "Копіювати",
                Location = new Point(320, 204),
                Size = new Size(88, 27)
            };
            btnCopy.Click += BtnCopy_Click;

            lblStrength = new Label
            {
                Text = "Надійність пароля: —",
                Location = new Point(12, 245),
                Size = new Size(396, 25),
                Font = new Font("Segoe UI", 9.5F, FontStyle.Bold)
            };

            Controls.Add(lblLength);
            Controls.Add(numLength);
            Controls.Add(chkDigits);
            Controls.Add(chkUpper);
            Controls.Add(chkSpecial);
            Controls.Add(btnGenerate);
            Controls.Add(txtPassword);
            Controls.Add(btnCopy);
            Controls.Add(lblStrength);
        }

        private void BtnGenerate_Click(object? sender, EventArgs e)
        {
            int length = (int)numLength.Value;

            // Базовий набір — малі літери завжди присутні
            string pool = LowerChars;
            bool useDigits = chkDigits.Checked;
            bool useUpper = chkUpper.Checked;
            bool useSpecial = chkSpecial.Checked;

            if (useDigits) pool += DigitChars;
            if (useUpper) pool += UpperChars;
            if (useSpecial) pool += SpecialChars;

            var passwordChars = new List<char>();

            // Гарантуємо, що в паролі буде хоча б по одному символу з кожної обраної категорії
            passwordChars.Add(PickRandomChar(LowerChars));
            if (useDigits) passwordChars.Add(PickRandomChar(DigitChars));
            if (useUpper) passwordChars.Add(PickRandomChar(UpperChars));
            if (useSpecial) passwordChars.Add(PickRandomChar(SpecialChars));

            while (passwordChars.Count < length)
            {
                passwordChars.Add(PickRandomChar(pool));
            }

            // Перемішуємо символи, щоб гарантовані символи не завжди стояли на початку
            ShuffleInPlace(passwordChars);

            // На випадок якщо гарантованих символів вийшло більше за задану довжину
            string result = new string(passwordChars.Take(length).ToArray());

            txtPassword.Text = result;
            lblStrength.Text = $"Надійність пароля: {EvaluateStrength(length, useDigits, useUpper, useSpecial)}";
        }

        private static char PickRandomChar(string source)
        {
            int index = RandomNumberGenerator.GetInt32(source.Length);
            return source[index];
        }

        private static void ShuffleInPlace(List<char> chars)
        {
            for (int i = chars.Count - 1; i > 0; i--)
            {
                int j = RandomNumberGenerator.GetInt32(i + 1);
                (chars[i], chars[j]) = (chars[j], chars[i]);
            }
        }

        private static string EvaluateStrength(int length, bool digits, bool upper, bool special)
        {
            int categories = 1 + (digits ? 1 : 0) + (upper ? 1 : 0) + (special ? 1 : 0);

            if (length >= 12 && categories >= 3) return "Висока";
            if (length >= 8 && categories >= 2) return "Середня";
            return "Низька";
        }

        private void BtnCopy_Click(object? sender, EventArgs e)
        {
            if (!string.IsNullOrEmpty(txtPassword.Text))
            {
                Clipboard.SetText(txtPassword.Text);
                MessageBox.Show("Пароль скопійовано в буфер обміну.", "Готово",
                    MessageBoxButtons.OK, MessageBoxIcon.Information);
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
