public class Indicator
{
    public Guid Id { get; set; }
    public string Name { get; set; } = string.Empty; // e.g., "Gross County Product"
    public string Category { get; set; } = string.Empty; // e.g., "Economy", "Agriculture"
    public string Unit { get; set; } = string.Empty; // e.g., "Millions KES", "Percentage"
    public string Description { get; set; } = string.Empty;
}