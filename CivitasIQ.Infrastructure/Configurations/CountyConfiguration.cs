using CivitasIQ.Domain;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace CivitasIQ.Infrastructure.Configurations;

public class CountyConfiguration : IEntityTypeConfiguration<County>
{
    public void Configure(EntityTypeBuilder<County> builder)
    {
        builder.ToTable("Counties");

        builder.HasKey(c => c.Id);

        builder.Property(c => c.Name)
            .IsRequired()
            .HasMaxLength(100);

        builder.Property(c => c.Region)
            .HasMaxLength(50);
        
        // Ensure county codes are unique
        builder.HasIndex(c => c.Code)
            .IsUnique();
        // PostGIS Geometry column configuration
    }
}

