using CivitasIQ.Application.DTOs;
using CivitasIQ.Application.Interfaces;
using Microsoft.EntityFrameworkCore;

namespace CivitasIQ.Infrastructure.Services;

public class AnalyticsService : IAnalyticsService
{
    private readonly ApplicationDbContext _context;

    public AnalyticsService(ApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<IEnumerable<MetricResponseDto>> GetCountyMetricsAsync(string indicatorName, int? year = null)
    {
        var query = _context.Metrics
            .AsNoTracking() // CRITICAL: Disables EF Core tracking for massive performance gains on read-only queries
            .Include(m => m.County)
            .Include(m => m.Indicator)
            .Where(m => m.Indicator.Name.ToLower() == indicatorName.ToLower());

        if (year.HasValue)
        {
            query = query.Where(m => m.Year == year.Value);
        }

        // Project directly into the DTO to save memory
        return await query
            .Select(m => new MetricResponseDto
            {
                CountyName = m.County.Name,
                Region = m.County.Region,
                Indicator = m.Indicator.Name,
                Year = m.Year,
                Value = m.Value,
                Unit = m.Indicator.Unit
            })
            .OrderBy(dto => dto.CountyName)
            .ThenBy(dto => dto.Year)
            .ToListAsync();
    }

    public async Task<IEnumerable<MetricResponseDto>> GetTopCountiesAsync(string indicatorName, int year, int count = 5)
    {
        return await _context.Metrics
            .AsNoTracking()
            .Include(m => m.County)
            .Include(m => m.Indicator)
            .Where(m => m.Indicator.Name.ToLower() == indicatorName.ToLower() && m.Year == year)
            .OrderByDescending(m => m.Value)
            .Take(count)
            .Select(m => new MetricResponseDto
            {
                CountyName = m.County.Name,
                Region = m.County.Region,
                Indicator = m.Indicator.Name,
                Year = m.Year,
                Value = m.Value,
                Unit = m.Indicator.Unit
            })
            .ToListAsync();
    }
}