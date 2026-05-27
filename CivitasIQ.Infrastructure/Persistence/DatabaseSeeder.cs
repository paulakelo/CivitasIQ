using CivitasIQ.Domain;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace CivitasIQ.Infrastructure.Persistence;

public static class DatabaseSeeder
{
    public static async Task SeedAsync(ApplicationDbContext context, ILogger logger)
    {
        try
        {
            // 1. Seed Indicators
            if (!await context.Indicators.AnyAsync())
            {
                logger.LogInformation("Seeding initial Indicators...");
                
                var indicators = new List<Indicator>
                {
                    new Indicator 
                    { 
                        Id = Guid.NewGuid(), 
                        Name = "Gross County Product", 
                        Category = "Economy", 
                        Unit = "Millions KES",
                        Description = "The total value of goods and services produced within a county."
                    },
                    new Indicator 
                    { 
                        Id = Guid.NewGuid(), 
                        Name = "Population", 
                        Category = "Demographics", 
                        Unit = "Persons",
                        Description = "Total number of individuals residing in the county."
                    }
                };

                await context.Indicators.AddRangeAsync(indicators);
                await context.SaveChangesAsync();
            }

            // 2. Seed Counties
            if (!await context.Counties.AnyAsync())
            {
                logger.LogInformation("Seeding 47 Kenyan Counties...");

                var counties = new List<County>
                {
                    new County { Id = Guid.NewGuid(), Code = 1, Name = "Mombasa", Region = "Coast" },
                    new County { Id = Guid.NewGuid(), Code = 2, Name = "Kwale", Region = "Coast" },
                    new County { Id = Guid.NewGuid(), Code = 3, Name = "Kilifi", Region = "Coast" },
                    new County { Id = Guid.NewGuid(), Code = 4, Name = "Tana River", Region = "Coast" },
                    new County { Id = Guid.NewGuid(), Code = 5, Name = "Lamu", Region = "Coast" },
                    new County { Id = Guid.NewGuid(), Code = 6, Name = "Taita Taveta", Region = "Coast" },
                    new County { Id = Guid.NewGuid(), Code = 7, Name = "Garissa", Region = "North Eastern" },
                    new County { Id = Guid.NewGuid(), Code = 8, Name = "Wajir", Region = "North Eastern" },
                    new County { Id = Guid.NewGuid(), Code = 9, Name = "Mandera", Region = "North Eastern" },
                    new County { Id = Guid.NewGuid(), Code = 10, Name = "Marsabit", Region = "Eastern" },
                    new County { Id = Guid.NewGuid(), Code = 11, Name = "Isiolo", Region = "Eastern" },
                    new County { Id = Guid.NewGuid(), Code = 12, Name = "Meru", Region = "Eastern" },
                    new County { Id = Guid.NewGuid(), Code = 13, Name = "Tharaka Nithi", Region = "Eastern" },
                    new County { Id = Guid.NewGuid(), Code = 14, Name = "Embu", Region = "Eastern" },
                    new County { Id = Guid.NewGuid(), Code = 15, Name = "Kitui", Region = "Eastern" },
                    new County { Id = Guid.NewGuid(), Code = 16, Name = "Machakos", Region = "Eastern" },
                    new County { Id = Guid.NewGuid(), Code = 17, Name = "Makueni", Region = "Eastern" },
                    new County { Id = Guid.NewGuid(), Code = 18, Name = "Nyandarua", Region = "Central" },
                    new County { Id = Guid.NewGuid(), Code = 19, Name = "Nyeri", Region = "Central" },
                    new County { Id = Guid.NewGuid(), Code = 20, Name = "Kirinyaga", Region = "Central" },
                    new County { Id = Guid.NewGuid(), Code = 21, Name = "Muranga", Region = "Central" },
                    new County { Id = Guid.NewGuid(), Code = 22, Name = "Kiambu", Region = "Central" },
                    new County { Id = Guid.NewGuid(), Code = 23, Name = "Turkana", Region = "Rift Valley" },
                    new County { Id = Guid.NewGuid(), Code = 24, Name = "West Pokot", Region = "Rift Valley" },
                    new County { Id = Guid.NewGuid(), Code = 25, Name = "Samburu", Region = "Rift Valley" },
                    new County { Id = Guid.NewGuid(), Code = 26, Name = "Trans Nzoia", Region = "Rift Valley" },
                    new County { Id = Guid.NewGuid(), Code = 27, Name = "Uasin Gishu", Region = "Rift Valley" },
                    new County { Id = Guid.NewGuid(), Code = 28, Name = "Elgeyo Marakwet", Region = "Rift Valley" },
                    new County { Id = Guid.NewGuid(), Code = 29, Name = "Nandi", Region = "Rift Valley" },
                    new County { Id = Guid.NewGuid(), Code = 30, Name = "Baringo", Region = "Rift Valley" },
                    new County { Id = Guid.NewGuid(), Code = 31, Name = "Laikipia", Region = "Rift Valley" },
                    new County { Id = Guid.NewGuid(), Code = 32, Name = "Nakuru", Region = "Rift Valley" },
                    new County { Id = Guid.NewGuid(), Code = 33, Name = "Narok", Region = "Rift Valley" },
                    new County { Id = Guid.NewGuid(), Code = 34, Name = "Kajiado", Region = "Rift Valley" },
                    new County { Id = Guid.NewGuid(), Code = 35, Name = "Kericho", Region = "Rift Valley" },
                    new County { Id = Guid.NewGuid(), Code = 36, Name = "Bomet", Region = "Rift Valley" },
                    new County { Id = Guid.NewGuid(), Code = 37, Name = "Kakamega", Region = "Western" },
                    new County { Id = Guid.NewGuid(), Code = 38, Name = "Vihiga", Region = "Western" },
                    new County { Id = Guid.NewGuid(), Code = 39, Name = "Bungoma", Region = "Western" },
                    new County { Id = Guid.NewGuid(), Code = 40, Name = "Busia", Region = "Western" },
                    new County { Id = Guid.NewGuid(), Code = 41, Name = "Siaya", Region = "Nyanza" },
                    new County { Id = Guid.NewGuid(), Code = 42, Name = "Kisumu", Region = "Nyanza" },
                    new County { Id = Guid.NewGuid(), Code = 43, Name = "Homa Bay", Region = "Nyanza" },
                    new County { Id = Guid.NewGuid(), Code = 44, Name = "Migori", Region = "Nyanza" },
                    new County { Id = Guid.NewGuid(), Code = 45, Name = "Kisii", Region = "Nyanza" },
                    new County { Id = Guid.NewGuid(), Code = 46, Name = "Nyamira", Region = "Nyanza" },
                    new County { Id = Guid.NewGuid(), Code = 47, Name = "Nairobi", Region = "Nairobi" }
                };

                await context.Counties.AddRangeAsync(counties);
                await context.SaveChangesAsync();
            }
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "An error occurred while seeding the database.");
            throw;
        }
    }
}