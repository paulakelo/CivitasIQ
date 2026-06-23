using CivitasIQ.Application.Interfaces;
using Microsoft.AspNetCore.Mvc;

namespace CivitasIQ.API.Controllers;

[ApiController]
[Route("api/[controller]")]
public class AnalyticsController : ControllerBase
{
    private readonly IAnalyticsService _analyticsService;

    // The Controller knows NOTHING about the database. It just asks the Interface for data.
    public AnalyticsController(IAnalyticsService analyticsService)
    {
        _analyticsService = analyticsService;
    }

    [HttpGet("metrics")]
    public async Task<IActionResult> GetMetrics([FromQuery] string indicator, [FromQuery] int? year)
    {
        if (string.IsNullOrWhiteSpace(indicator))
            return BadRequest("Indicator name is required.");

        var data = await _analyticsService.GetCountyMetricsAsync(indicator, year);
        return Ok(data);
    }

    [HttpGet("top-performers")]
    public async Task<IActionResult> GetTopPerformers([FromQuery] string indicator, [FromQuery] int year, [FromQuery] int count = 5)
    {
        if (string.IsNullOrWhiteSpace(indicator))
            return BadRequest("Indicator name is required.");

        var data = await _analyticsService.GetTopCountiesAsync(indicator, year, count);
        return Ok(data);
    }
}