public class County
{
    public Guid Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public int Code { get; set; } // e.g., 047 for Nairobi
    public string Region { get; set; } = string.Empty;
    public double AreaSqKm { get; set; }
    
    // Navigation property
    public ICollection<Metric> Metrics { get; set; } = new List<Metric>();
}