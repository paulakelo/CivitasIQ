using CivitasIQ.Domain;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace CivitasIQ.Infrastructure.Configurations;

public class IndicatorConfiguration : IEntityTypeConfiguration<Indicator>
{
    public void Configure(EntityTypeBuilder<Indicator> builder)
    {
        builder.ToTable("Indicators");

        builder.HasKey(i => i.Id);

        builder.Property(i => i.Name)
            .IsRequired()
            .HasMaxLength(200);

        builder.Property(i => i.Category)
            .IsRequired()
            .HasMaxLength(100); // e.g., "Economy"

        builder.Property(i => i.Unit)
            .HasMaxLength(50); // e.g. "Millions KES", "%"
    }
}