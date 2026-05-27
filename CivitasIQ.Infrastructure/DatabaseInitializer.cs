using CivitasIQ.Infrastructure.Persistence;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;

namespace CivitasIQ.Infrastructure;

public static class DatabaseInitializer
{
    // Notice we changed 'WebApplication app' to 'IServiceProvider serviceProvider'
    public static async Task InitializeDatabaseAsync(this IServiceProvider serviceProvider)
    {
        // Create the scope directly from the service provider
        using var scope = serviceProvider.CreateScope();
        var services = scope.ServiceProvider;

        try
        {
            var context = services.GetRequiredService<ApplicationDbContext>();
            var logger = services.GetRequiredService<ILogger<ApplicationDbContext>>();

            // 1. Automatically apply any pending migrations
            if (context.Database.IsRelational())
            {
                await context.Database.MigrateAsync();
            }

            // 2. Seed the data
            await DatabaseSeeder.SeedAsync(context, logger);
        }
        catch (Exception ex)
        {
            var logger = services.GetRequiredService<ILogger<ApplicationDbContext>>();
            logger.LogError(ex, "An error occurred during database initialization.");
        }
    }
}