namespace QuizFileSystems
{
    public class MainForm : Form
    {
        private const int SecondsPerQuestion = 30;
        private const int TotalQuestions = 15;

        private readonly List<Question> _questions = QuestionBank.GetQuestions();
        private int _currentIndex = 0;
        private int _score = 0;
        private int _timeLeft = SecondsPerQuestion;

        private System.Windows.Forms.Timer _timer = null!;

        private Label lblTitle = null!;
        private Label lblProgress = null!;
        private Label lblTimer = null!;
        private ProgressBar pbTime = null!;
        private Label lblQuestion = null!;
        private RadioButton[] _options = null!;
        private Button btnNext = null!;
        private Panel panelQuiz = null!;
        private Panel panelResult = null!;
        private Label lblResultTitle = null!;
        private Label lblResultDetails = null!;
        private Button btnRestart = null!;
        private Button btnExit = null!;
        private Button btnStart = null!;
        private Panel panelStart = null!;
        private Label lblStartInfo = null!;

        public MainForm()
        {
            BuildUi();
            ShowStartPanel();
        }

        private void BuildUi()
        {
            Text = "Квіз: Файлові системи";
            ClientSize = new Size(700, 520);
            FormBorderStyle = FormBorderStyle.FixedSingle;
            MaximizeBox = false;
            StartPosition = FormStartPosition.CenterScreen;
            BackColor = Color.White;
            Font = new Font("Segoe UI", 10F);

            _timer = new System.Windows.Forms.Timer { Interval = 1000 };
            _timer.Tick += Timer_Tick;

            BuildStartPanel();
            BuildQuizPanel();
            BuildResultPanel();

            Controls.Add(panelStart);
            Controls.Add(panelQuiz);
            Controls.Add(panelResult);
        }

        private void BuildStartPanel()
        {
            panelStart = new Panel
            {
                Location = new Point(0, 0),
                Size = new Size(700, 520),
                Visible = true
            };

            var lblHeader = new Label
            {
                Text = "КВІЗ: ФАЙЛОВІ СИСТЕМИ",
                Location = new Point(40, 60),
                Size = new Size(620, 45),
                TextAlign = ContentAlignment.MiddleCenter,
                Font = new Font("Segoe UI", 18F, FontStyle.Bold),
                ForeColor = Color.FromArgb(30, 60, 110)
            };

            lblStartInfo = new Label
            {
                Text =
                    "Тест складається з 15 питань з варіантами відповідей.\n\n" +
                    "На кожне питання дається 30 секунд.\n" +
                    "Якщо час вичерпано, автоматично відбувається перехід\n" +
                    "до наступного питання, а відповідь не зараховується.\n\n" +
                    "Наприкінці буде виставлена оцінка за 12-бальною системою.",
                Location = new Point(60, 130),
                Size = new Size(580, 200),
                TextAlign = ContentAlignment.MiddleCenter,
                Font = new Font("Segoe UI", 11F)
            };

            btnStart = new Button
            {
                Text = "Почати тест",
                Location = new Point(250, 350),
                Size = new Size(200, 50),
                BackColor = Color.FromArgb(30, 60, 110),
                ForeColor = Color.White,
                FlatStyle = FlatStyle.Flat,
                Font = new Font("Segoe UI", 12F, FontStyle.Bold)
            };
            btnStart.Click += BtnStart_Click;

            panelStart.Controls.Add(lblHeader);
            panelStart.Controls.Add(lblStartInfo);
            panelStart.Controls.Add(btnStart);
        }

        private void BuildQuizPanel()
        {
            panelQuiz = new Panel
            {
                Location = new Point(0, 0),
                Size = new Size(700, 520),
                Visible = false
            };

            lblTitle = new Label
            {
                Text = "Тема: Файлові системи",
                Location = new Point(20, 15),
                Size = new Size(400, 25),
                Font = new Font("Segoe UI", 11F, FontStyle.Bold),
                ForeColor = Color.FromArgb(30, 60, 110)
            };

            lblProgress = new Label
            {
                Text = "Питання 1 з 15",
                Location = new Point(460, 15),
                Size = new Size(210, 25),
                TextAlign = ContentAlignment.MiddleRight,
                Font = new Font("Segoe UI", 10F, FontStyle.Bold)
            };

            lblTimer = new Label
            {
                Text = "Залишилось часу: 30 с",
                Location = new Point(20, 50),
                Size = new Size(300, 25),
                Font = new Font("Segoe UI", 10F, FontStyle.Bold),
                ForeColor = Color.DarkGreen
            };

            pbTime = new ProgressBar
            {
                Location = new Point(20, 78),
                Size = new Size(650, 14),
                Minimum = 0,
                Maximum = SecondsPerQuestion,
                Value = SecondsPerQuestion
            };

            lblQuestion = new Label
            {
                Text = "",
                Location = new Point(20, 110),
                Size = new Size(650, 70),
                Font = new Font("Segoe UI", 12F, FontStyle.Bold)
            };

            _options = new RadioButton[4];
            for (int i = 0; i < 4; i++)
            {
                _options[i] = new RadioButton
                {
                    Location = new Point(40, 200 + i * 55),
                    Size = new Size(620, 45),
                    Font = new Font("Segoe UI", 10.5F),
                    AutoSize = false
                };
                panelQuiz.Controls.Add(_options[i]);
            }

            btnNext = new Button
            {
                Text = "Відповісти",
                Location = new Point(470, 435),
                Size = new Size(200, 45),
                BackColor = Color.FromArgb(30, 60, 110),
                ForeColor = Color.White,
                FlatStyle = FlatStyle.Flat,
                Font = new Font("Segoe UI", 11F, FontStyle.Bold)
            };
            btnNext.Click += BtnNext_Click;

            panelQuiz.Controls.Add(lblTitle);
            panelQuiz.Controls.Add(lblProgress);
            panelQuiz.Controls.Add(lblTimer);
            panelQuiz.Controls.Add(pbTime);
            panelQuiz.Controls.Add(lblQuestion);
            panelQuiz.Controls.Add(btnNext);
        }

        private void BuildResultPanel()
        {
            panelResult = new Panel
            {
                Location = new Point(0, 0),
                Size = new Size(700, 520),
                Visible = false
            };

            lblResultTitle = new Label
            {
                Text = "РЕЗУЛЬТАТ ТЕСТУВАННЯ",
                Location = new Point(40, 50),
                Size = new Size(620, 45),
                TextAlign = ContentAlignment.MiddleCenter,
                Font = new Font("Segoe UI", 18F, FontStyle.Bold),
                ForeColor = Color.FromArgb(30, 60, 110)
            };

            lblResultDetails = new Label
            {
                Text = "",
                Location = new Point(60, 120),
                Size = new Size(580, 240),
                TextAlign = ContentAlignment.MiddleCenter,
                Font = new Font("Segoe UI", 12F)
            };

            btnRestart = new Button
            {
                Text = "Пройти ще раз",
                Location = new Point(130, 400),
                Size = new Size(200, 45),
                BackColor = Color.FromArgb(30, 60, 110),
                ForeColor = Color.White,
                FlatStyle = FlatStyle.Flat,
                Font = new Font("Segoe UI", 11F, FontStyle.Bold)
            };
            btnRestart.Click += BtnRestart_Click;

            btnExit = new Button
            {
                Text = "Вихід",
                Location = new Point(370, 400),
                Size = new Size(200, 45),
                FlatStyle = FlatStyle.Flat,
                Font = new Font("Segoe UI", 11F, FontStyle.Bold)
            };
            btnExit.Click += (s, e) => Close();

            panelResult.Controls.Add(lblResultTitle);
            panelResult.Controls.Add(lblResultDetails);
            panelResult.Controls.Add(btnRestart);
            panelResult.Controls.Add(btnExit);
        }

        private void ShowStartPanel()
        {
            panelStart.Visible = true;
            panelQuiz.Visible = false;
            panelResult.Visible = false;
        }

        private void BtnStart_Click(object? sender, EventArgs e)
        {
            _currentIndex = 0;
            _score = 0;

            panelStart.Visible = false;
            panelResult.Visible = false;
            panelQuiz.Visible = true;

            LoadQuestion();
        }

        private void LoadQuestion()
        {
            Question question = _questions[_currentIndex];

            lblProgress.Text = $"Питання {_currentIndex + 1} з {TotalQuestions}";
            lblQuestion.Text = question.Text;

            for (int i = 0; i < _options.Length; i++)
            {
                _options[i].Text = question.Options[i];
                _options[i].Checked = false;
                _options[i].Enabled = true;
            }

            btnNext.Text = _currentIndex == TotalQuestions - 1 ? "Завершити тест" : "Відповісти";

            _timeLeft = SecondsPerQuestion;
            pbTime.Value = SecondsPerQuestion;
            UpdateTimerLabel();
            _timer.Start();
        }

        private void Timer_Tick(object? sender, EventArgs e)
        {
            _timeLeft--;

            if (_timeLeft <= 0)
            {
                _timer.Stop();
                pbTime.Value = 0;
                lblTimer.Text = "Час вичерпано!";
                lblTimer.ForeColor = Color.DarkRed;

                MessageBox.Show(
                    "Час на відповідь вичерпано. Переходимо до наступного питання.",
                    "Час вийшов",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Information);

                GoToNextQuestion();
                return;
            }

            pbTime.Value = _timeLeft;
            UpdateTimerLabel();
        }

        private void UpdateTimerLabel()
        {
            lblTimer.Text = $"Залишилось часу: {_timeLeft} с";

            if (_timeLeft <= 5)
            {
                lblTimer.ForeColor = Color.DarkRed;
            }
            else if (_timeLeft <= 10)
            {
                lblTimer.ForeColor = Color.DarkOrange;
            }
            else
            {
                lblTimer.ForeColor = Color.DarkGreen;
            }
        }

        private void BtnNext_Click(object? sender, EventArgs e)
        {
            int selectedIndex = -1;
            for (int i = 0; i < _options.Length; i++)
            {
                if (_options[i].Checked)
                {
                    selectedIndex = i;
                    break;
                }
            }

            if (selectedIndex == -1)
            {
                MessageBox.Show(
                    "Оберіть один з варіантів відповіді.",
                    "Увага",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Warning);
                return;
            }

            _timer.Stop();

            if (selectedIndex == _questions[_currentIndex].CorrectIndex)
            {
                _score++;
            }

            GoToNextQuestion();
        }

        private void GoToNextQuestion()
        {
            _currentIndex++;

            if (_currentIndex >= TotalQuestions)
            {
                ShowResult();
            }
            else
            {
                LoadQuestion();
            }
        }

        private void ShowResult()
        {
            _timer.Stop();

            panelQuiz.Visible = false;
            panelResult.Visible = true;

            int grade = CalculateGrade(_score);
            string comment = GetComment(grade);
            double percent = (double)_score / TotalQuestions * 100;

            lblResultDetails.Text =
                $"Правильних відповідей: {_score} з {TotalQuestions}\n\n" +
                $"Результат: {percent:F1} %\n\n" +
                $"Оцінка за 12-бальною системою: {grade}\n\n" +
                $"{comment}";

            if (grade >= 10)
            {
                lblResultDetails.ForeColor = Color.DarkGreen;
            }
            else if (grade >= 7)
            {
                lblResultDetails.ForeColor = Color.FromArgb(30, 60, 110);
            }
            else if (grade >= 4)
            {
                lblResultDetails.ForeColor = Color.DarkOrange;
            }
            else
            {
                lblResultDetails.ForeColor = Color.DarkRed;
            }
        }

        private static int CalculateGrade(int score)
        {
            double ratio = (double)score / TotalQuestions;
            int grade = (int)Math.Round(ratio * 12, MidpointRounding.AwayFromZero);

            if (grade < 1 && score > 0)
            {
                grade = 1;
            }

            if (score == 0)
            {
                grade = 1;
            }

            if (grade > 12)
            {
                grade = 12;
            }

            return grade;
        }

        private static string GetComment(int grade)
        {
            if (grade >= 10)
            {
                return "Високий рівень. Тему засвоєно відмінно!";
            }
            if (grade >= 7)
            {
                return "Достатній рівень. Хороший результат.";
            }
            if (grade >= 4)
            {
                return "Середній рівень. Варто повторити матеріал.";
            }
            return "Початковий рівень. Потрібно ґрунтовно вивчити тему.";
        }

        private void BtnRestart_Click(object? sender, EventArgs e)
        {
            _currentIndex = 0;
            _score = 0;
            lblResultDetails.ForeColor = Color.Black;

            panelResult.Visible = false;
            panelQuiz.Visible = true;

            LoadQuestion();
        }
    }
}
