using CivitasIQ.Domain;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace CivitasIQ.Infrastructure.Configurations;

public class MetricConfiguration : IEntityTypeConfiguration<Metric>
{
    public void Configure(EntityTypeBuilder<Metric> builder)
    {
        builder.ToTable("Metrics");
        
        builder.HasKey(m => m.Id);

        builder.Property(m => m.Value)
            .HasPrecision(18, 4);

        builder.Property(m => m.Source)
            .HasMaxLength(200);

        builder.HasOne(m => m.County)
        .WithMany(c => c.Metrics)
        .HasForeignKey(m => m.CountyId)
        .OnDelete(DeleteBehavior.Cascade);

        builder.HasIndex(m => new { m.CountyId, m.IndicatorId, m.Year })
             .IsUnique();
    }
}