namespace CivitasIQ.Application.DTOs;

public class MetricResponseDto
{
	public string CountyName { get; set; } = string.Empty;
	public string Region { get; set; } = string.Empty;
	public string Indicator { get; set; } = string.Empty;
	public int Year { get; set; }
	public decimal Value { get; set; }
	public string Unit { get; set; } = string.Empty;
}