namespace QuizApp;

public class Question
{
    public string Text { get; init; } = "";
    public string[] Options { get; init; } = Array.Empty<string>();
    public int[] Correct { get; init; } = Array.Empty<int>();

    // Якщо правильних відповідей більше однієї — показуємо CheckBox, інакше RadioButton
    public bool IsMultiple => Correct.Length > 1;
}
