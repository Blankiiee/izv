namespace QuizApp;

public class MainForm : Form
{
    private readonly List<Question> questions = new()
    {
        new Question
        {
            Text = "Який принцип ООП дозволяє приховувати внутрішню реалізацію класу?",
            Options = new[] { "Наслідування", "Інкапсуляція", "Поліморфізм", "Агрегація" },
            Correct = new[] { 1 }
        },
        new Question
        {
            Text = "Які з перелічених модифікаторів доступу існують у C#? (кілька відповідей)",
            Options = new[] { "public", "private", "friend", "internal", "protected" },
            Correct = new[] { 0, 1, 3, 4 }
        },
        new Question
        {
            Text = "Який символ використовується в C# для вказання базового класу?",
            Options = new[] { "->", ":", "::", "=>" },
            Correct = new[] { 1 }
        },
        new Question
        {
            Text = "Які з перелічених типів є типами значень (value types)? (кілька відповідей)",
            Options = new[] { "int", "string", "bool", "DateTime" },
            Correct = new[] { 0, 2, 3 }
        },
        new Question
        {
            Text = "Який спеціальний метод викликається під час створення об'єкта?",
            Options = new[] { "Деструктор", "Конструктор", "Індексатор", "Ітератор" },
            Correct = new[] { 1 }
        },
        new Question
        {
            Text = "Яке ключове слово у базовому класі дозволяє перевизначити метод у нащадках?",
            Options = new[] { "virtual", "static", "sealed", "const" },
            Correct = new[] { 0 }
        }
    };

    private int currentIndex;
    private int score;

    private Label lblProgress = new();
    private Label lblQuestion = new();
    private Label lblHint = new();
    private Panel pnlOptions = new();
    private Button btnNext = new();

    public MainForm()
    {
        Text = "Тест з ООП та C#";
        Width = 600;
        Height = 460;
        StartPosition = FormStartPosition.CenterScreen;
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = false;

        lblProgress.Location = new Point(20, 15);
        lblProgress.AutoSize = true;
        lblProgress.Font = new Font(Font, FontStyle.Bold);

        lblQuestion.Location = new Point(20, 45);
        lblQuestion.Size = new Size(540, 55);
        lblQuestion.Font = new Font(Font.FontFamily, 11, FontStyle.Regular);

        lblHint.Location = new Point(20, 105);
        lblHint.AutoSize = true;
        lblHint.ForeColor = Color.Gray;

        pnlOptions.Location = new Point(20, 135);
        pnlOptions.Size = new Size(540, 210);

        btnNext.Location = new Point(410, 360);
        btnNext.Size = new Size(150, 36);
        btnNext.Click += BtnNext_Click;

        Controls.AddRange(new Control[] { lblProgress, lblQuestion, lblHint, pnlOptions, btnNext });

        ShowQuestion();
    }

    private void ShowQuestion()
    {
        var q = questions[currentIndex];

        lblProgress.Text = $"Питання {currentIndex + 1} з {questions.Count}";
        lblQuestion.Text = q.Text;
        lblHint.Text = q.IsMultiple ? "Оберіть усі правильні варіанти" : "Оберіть один варіант";
        btnNext.Text = currentIndex == questions.Count - 1 ? "Завершити тест" : "Далі";

        pnlOptions.Controls.Clear();

        for (int i = 0; i < q.Options.Length; i++)
        {
            Control option = q.IsMultiple
                ? new CheckBox()
                : new RadioButton();

            option.Text = q.Options[i];
            option.Location = new Point(5, 5 + i * 36);
            option.Size = new Size(520, 30);
            option.Font = new Font(Font.FontFamily, 10);
            pnlOptions.Controls.Add(option);
        }
    }

    private HashSet<int> GetSelected()
    {
        var selected = new HashSet<int>();
        for (int i = 0; i < pnlOptions.Controls.Count; i++)
        {
            bool isChecked = pnlOptions.Controls[i] switch
            {
                CheckBox cb => cb.Checked,
                RadioButton rb => rb.Checked,
                _ => false
            };

            if (isChecked)
                selected.Add(i);
        }
        return selected;
    }

    private void BtnNext_Click(object? sender, EventArgs e)
    {
        var selected = GetSelected();

        if (selected.Count == 0)
        {
            MessageBox.Show("Оберіть хоча б одну відповідь", "Увага", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return;
        }

        // Бал нараховується лише за повністю правильний набір відповідей
        if (selected.SetEquals(questions[currentIndex].Correct))
            score++;

        currentIndex++;

        if (currentIndex < questions.Count)
            ShowQuestion();
        else
            ShowResult();
    }

    private void ShowResult()
    {
        int total = questions.Count;
        double percent = score * 100.0 / total;

        string verdict = percent switch
        {
            >= 90 => "Відмінно!",
            >= 70 => "Добре",
            >= 50 => "Задовільно",
            _ => "Потрібно повторити матеріал"
        };

        var answer = MessageBox.Show(
            $"Правильних відповідей: {score} з {total}\n" +
            $"Результат: {percent:F0}%\n" +
            $"Оцінка: {verdict}\n\n" +
            "Пройти тест ще раз?",
            "Результат тесту",
            MessageBoxButtons.YesNo,
            MessageBoxIcon.Information);

        if (answer == DialogResult.Yes)
        {
            currentIndex = 0;
            score = 0;
            ShowQuestion();
        }
        else
        {
            Close();
        }
    }
}
