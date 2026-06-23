using CivitasIQ.Application.DTOs;

namespace CivitasIQ.Application.Interfaces;

public interface IAnalyticsService 
{
	Task<IEnumerable<MetricResponseDto>> GetCountyMetricsAsync(string indicatorName, int? year = null);
	Task<IEnumerable<MetricResponseDto>> GetTopCountiesAsync(string indicatorName, int year, int count = 5);
}