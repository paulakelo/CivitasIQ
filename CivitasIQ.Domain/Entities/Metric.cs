public class Metric
{
    public Guid Id { get; set; }
    public Guid CountyId { get; set; }
    public Guid IndicatorId { get; set; }
    public int Year { get; set; }
    public decimal Value { get; set; }
    public string Source { get; set; } = string.Empty; // e.g., "KNBS 2023"

    // Navigation properties
    public County County { get; set; } = null!;
    public Indicator Indicator { get; set; } = null!;
}